"""
Enhanced Authentication System for Streamlit App with BYOK Support

🔐 SECURITY DESIGN:
- Admin users: Pre-configured API keys stored locally at:
  C:\2025_AIIncubator\aecoa\.streamlit\secrets.toml
- Public users: BYOK (Bring Your Own Key) - keys stored in session only
- secrets.toml is git-ignored and never committed for security

🎯 USER TYPES:
- 'admin': Access to pre-configured OpenAI & GovTech API keys
- 'public': Must provide their own API keys via BYOK interface

🔑 KEY STORAGE:
- Admin keys: Persistent local storage (secrets.toml)
- BYOK keys: Session-only storage (cleared on logout)
- All keys validated before use

Supports both admin users (with pre-configured API keys) and public users (BYOK)
"""

import streamlit as st
import hashlib
import hmac
from typing import Dict, List, Optional, Tuple
import requests
import json

class StreamlitAuth:
    def __init__(self):
        self.users = self._load_users()
        self.admin_users = ['admin']  # Users with access to pre-configured API keys
    
    def is_admin_user(self, username: str) -> bool:
        """Check if user is an admin with access to pre-configured API keys"""
        return username in self.admin_users
    
    def get_user_type(self, username: str) -> str:
        """Get user type: 'admin' (pre-configured keys) or 'public' (BYOK)"""
        return 'admin' if self.is_admin_user(username) else 'public'
    
    def get_admin_api_keys(self) -> Dict[str, Dict]:
        """Get pre-configured API keys for admin users from local secrets.toml
        
        Keys are stored securely at:
        C:\\2025_AIIncubator\\aecoa\\.streamlit\\secrets.toml
        
        This file is ignored by git and never committed to ensure security.
        """
        try:
            api_keys = {}
            
            # Get OpenAI keys from local secrets
            if hasattr(st, 'secrets') and 'openai' in st.secrets:
                api_keys['openai'] = {
                    'api_key': st.secrets['openai'].get('api_key', ''),
                    'base_url': st.secrets['openai'].get('base_url', 'https://api.openai.com/v1'),
                    'model': st.secrets['openai'].get('model', 'gpt-4o-mini')
                }
            
            # Get GovTech keys from local secrets
            if hasattr(st, 'secrets') and 'govtech' in st.secrets:
                govtech_base_url = st.secrets['govtech'].get(
                    'base_url', 
                    'https://llmaas.govtext.gov.sg/gateway'
                )
                api_keys['govtech'] = {
                    'api_key': st.secrets['govtech'].get('api_key', ''),
                    'base_url': govtech_base_url,
                    'model': st.secrets['govtech'].get('model', 'gpt-4')
                }
            
            return api_keys
        except Exception as e:
            st.error(f"Error loading admin API keys from local secrets: {e}")
            st.info("""
            **Admin keys should be configured in:**
            `C:\\2025_AIIncubator\\aecoa\\.streamlit\\secrets.toml`
            
            This file is private and never committed to git.
            """)
            return {}
    
    def validate_api_key(self, provider: str, api_key: str, base_url: str = None) -> Tuple[bool, str]:
        """Validate an API key for a specific provider"""
        if not api_key or not api_key.strip():
            return False, "API key is empty"
        
        try:
            if provider.lower() == 'openai':
                # Test OpenAI API key
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                url = f"{base_url or 'https://api.openai.com/v1'}/models"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return True, "Valid OpenAI API key"
                elif response.status_code == 401:
                    return False, "Invalid OpenAI API key"
                else:
                    return False, f"OpenAI API error: {response.status_code}"
                    
            elif provider.lower() == 'govtech':
                # Test GovTech API key
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                # Use a simple test endpoint or model list
                url = f"{base_url or 'https://llmaas.govtext.gov.sg/gateway'}/models"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    return True, "Valid GovTech API key"
                elif response.status_code == 401:
                    return False, "Invalid GovTech API key"
                else:
                    return False, f"GovTech API error: {response.status_code}"
            
            else:
                return False, f"Unsupported provider: {provider}"
                
        except requests.exceptions.Timeout:
            return False, f"Timeout testing {provider} API key"
        except requests.exceptions.RequestException as e:
            return False, f"Network error testing {provider} API key: {e}"
        except Exception as e:
            return False, f"Error validating {provider} API key: {e}"
    
    def _load_users(self) -> Dict[str, str]:
        """Load users from secrets.toml or return default users"""
        try:
            # Try to load from Streamlit secrets
            if hasattr(st, 'secrets') and 'auth' in st.secrets:
                users = {}
                for user_key, user_data in st.secrets['auth'].items():
                    if isinstance(user_data, dict) and 'password' in user_data:
                        # Handle structured format: {username: {password: "pass", role: "role"}}
                        users[user_key] = user_data['password']
                    else:
                        # Handle simple username: password format from secrets.toml
                        users[user_key] = str(user_data)
                return users
            else:
                # No auth section in secrets - provide guidance
                st.error("⚠️ No [auth] section found in secrets.toml")
                st.info("""
                **Please add authentication section to `.streamlit/secrets.toml`:**
                
                ```toml
                [auth]
                admin = "your_admin_password"
                user = "your_user_password"
                ```
                """)
                return {}
        except Exception as e:
            # Show error and guidance instead of hardcoded fallback
            st.error(f"❌ Error loading authentication from secrets.toml: {str(e)}")
            st.info("""
            **Please check your `.streamlit/secrets.toml` file format:**
            
            ```toml
            [auth]
            admin = "your_secure_admin_password"
            user = "your_secure_user_password"
            manager = "another_password"
            ```
            """)
            return {}
    
    def show_byok_interface(self, username: str) -> Dict[str, Dict]:
        """Show BYOK interface for public users to input their API keys"""
        st.markdown("### 🔑 Bring Your Own Key (BYOK)")
        st.markdown("Enter your API keys to use AI services. Keys are only stored for this session.")
        
        user_api_keys = {}
        
        # OpenAI Configuration
        with st.expander("🤖 OpenAI Configuration", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                openai_key = st.text_input(
                    "OpenAI API Key", 
                    type="password", 
                    placeholder="sk-...",
                    key="openai_api_key",
                    help="Get your key from https://platform.openai.com/"
                )
            with col2:
                openai_model = st.selectbox(
                    "Model",
                    ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                    key="openai_model"
                )
            
            if openai_key:
                if st.button("Test OpenAI Key", key="test_openai"):
                    with st.spinner("Testing OpenAI API key..."):
                        is_valid, message = self.validate_api_key("openai", openai_key)
                        if is_valid:
                            st.success(f"✅ {message}")
                            user_api_keys['openai'] = {
                                'api_key': openai_key,
                                'base_url': 'https://api.openai.com/v1',
                                'model': openai_model
                            }
                        else:
                            st.error(f"❌ {message}")
        
        # GovTech Configuration
        with st.expander("🏛️ GovTech AI Configuration", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                govtech_key = st.text_input(
                    "GovTech API Key", 
                    type="password", 
                    placeholder="sk-...",
                    key="govtech_api_key",
                    help="Get your key from GovTech AI portal"
                )
            with col2:
                govtech_model = st.selectbox(
                    "Model",
                    ["gpt-4", "gpt-3.5-turbo", "govtech-llm-v1"],
                    key="govtech_model"
                )
            
            if govtech_key:
                if st.button("Test GovTech Key", key="test_govtech"):
                    with st.spinner("Testing GovTech API key..."):
                        base_url = "https://llmaas.govtext.gov.sg/gateway"
                        is_valid, message = self.validate_api_key("govtech", govtech_key, base_url)
                        if is_valid:
                            st.success(f"✅ {message}")
                            user_api_keys['govtech'] = {
                                'api_key': govtech_key,
                                'base_url': base_url,
                                'model': govtech_model
                            }
                        else:
                            st.error(f"❌ {message}")
        
        # Local Ollama Option
        with st.expander("🖥️ Local Ollama (Free)", expanded=False):
            st.markdown("""
            **Use local AI models (no API key needed)**
            - Install Ollama: https://ollama.ai/
            - Download models: `ollama pull llama3.2`
            - No costs, complete privacy
            """)
            
            use_ollama = st.checkbox("Use Local Ollama", key="use_ollama")
            if use_ollama:
                ollama_host = st.text_input("Ollama Host", value="http://localhost:11434", key="ollama_host")
                ollama_model = st.text_input("Model Name", value="llama3.2:latest", key="ollama_model")
                
                user_api_keys['ollama'] = {
                    'host': ollama_host,
                    'model': ollama_model
                }
        
        # Save keys to session
        if user_api_keys:
            st.session_state[f'user_api_keys_{username}'] = user_api_keys
            
    def _load_users(self) -> Dict[str, str]:
        """Load users from secrets.toml or return default users"""
        try:
            # Try to load from Streamlit secrets
            if hasattr(st, 'secrets') and 'auth' in st.secrets:
                users = {}
                for user_key, user_data in st.secrets['auth'].items():
                    if isinstance(user_data, dict) and 'password' in user_data:
                        # Handle structured format: {username: {password: "pass", role: "role"}}
                        users[user_key] = user_data['password']
                    else:
                        # Handle simple username: password format from secrets.toml
                        users[user_key] = str(user_data)
                return users
            else:
                # No auth section in secrets - provide guidance
                st.error("⚠️ No [auth] section found in secrets.toml")
                st.info("""
                **Please add authentication section to `.streamlit/secrets.toml`:**
                
                ```toml
                [auth]
                admin = "your_admin_password"
                user = "your_user_password"
                ```
                """)
                return {}
        except Exception as e:
            # Show error and guidance instead of hardcoded fallback
            st.error(f"❌ Error loading authentication from secrets.toml: {str(e)}")
            st.info("""
            **Please check your `.streamlit/secrets.toml` file format:**
            
            ```toml
            [auth]
            admin = "your_secure_admin_password"
            user = "your_secure_user_password"
            manager = "another_password"
            ```
            """)
            return {}
        except Exception as e:
            # Show error and guidance instead of hardcoded fallback
            st.error(f"❌ Error loading authentication from secrets.toml: {str(e)}")
            st.info("""
            **Please check your `.streamlit/secrets.toml` file format:**
            
            ```toml
            [auth]
            admin = "your_secure_admin_password"
            user = "your_secure_user_password"
            manager = "another_password"
            ```
            """)
            return {}
    
    def get_user_api_keys(self, username: str) -> Dict[str, Dict]:
        """Get API keys for a user (admin: pre-configured, public: BYOK)"""
        if self.is_admin_user(username):
            # Admin users get pre-configured keys
            return self.get_admin_api_keys()
        else:
            # Public users use BYOK keys stored in session
            return st.session_state.get(f'user_api_keys_{username}', {})
    
    def show_api_key_status(self, username: str):
        """Show API key status for current user"""
        user_type = self.get_user_type(username)
        api_keys = self.get_user_api_keys(username)
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔑 API Key Status")
        st.sidebar.markdown(f"**User Type:** {user_type.title()}")
        
        if user_type == 'admin':
            st.sidebar.success("🔐 Using pre-configured admin keys")
            st.sidebar.info("🏠 Keys stored locally at:\n`C:\\2025_AIIncubator\\aecoa\\.streamlit\\secrets.toml`")
            for provider, config in api_keys.items():
                if config.get('api_key'):
                    st.sidebar.success(f"✅ {provider.title()}: Ready")
                else:
                    st.sidebar.error(f"❌ {provider.title()}: Not configured")
        else:
            st.sidebar.info("🔑 BYOK Mode - Configure your API keys")
            if api_keys:
                for provider in api_keys:
                    st.sidebar.success(f"✅ {provider.title()}: Configured")
            else:
                st.sidebar.warning("⚠️ No API keys configured")
                if st.sidebar.button("Configure API Keys"):
                    st.session_state['show_byok_setup'] = True
                    st.rerun()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verify a password against its hash"""
        # Check if stored password is already hashed (64 chars = SHA-256 hex)
        if len(stored_password) == 64:
            return hmac.compare_digest(stored_password, self._hash_password(provided_password))
        else:
            # Plain text comparison for simple setup
            return hmac.compare_digest(stored_password, provided_password)
    
    def login_form(self) -> bool:
        """Display login form and handle authentication"""
        
        # Check if already authenticated
        if st.session_state.get('authenticated', False):
            username = st.session_state.get('username', '')
            
            # Show BYOK setup for public users if requested
            if (st.session_state.get('show_byok_setup', False) and 
                not self.is_admin_user(username)):
                st.session_state['show_byok_setup'] = False
                self.show_byok_interface(username)
                return True
            
            return True
        
        # Create login form
        st.markdown("# 🔐 AEC Compliance Analysis - Login Required")
        st.markdown("Please log in to access the application and protect API resources.")
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### Please Enter Your Credentials")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input(
                    "Password", 
                    type="password", 
                    placeholder="Enter your password"
                )
                submit_button = st.form_submit_button("🚪 Login", use_container_width=True)
        
        # Handle login attempt
        if submit_button:
            if len(self.users) == 0:
                st.error("❌ No users configured in secrets.toml. Please check your configuration.")
                return False
            elif self.authenticate(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                
                # Show appropriate success message based on user type
                user_type = self.get_user_type(username)
                if user_type == 'admin':
                    st.success("✅ Admin login successful! Using pre-configured API keys.")
                else:
                    st.success("✅ Login successful! You can now configure your API keys (BYOK).")
                    st.session_state['show_byok_setup'] = True
                
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Please try again.")
                return False
        
        # Show setup instructions
        with st.expander("🔧 Setup Instructions for Administrators", expanded=False):
            st.markdown("""
            **To configure users, add to `.streamlit/secrets.toml`:**
            
            ```toml
            [auth]
            admin = "your_secure_admin_password"
            user = "your_secure_user_password"
            manager = "manager_password"
            ```
            
            **Current Configuration Status:**
            """)
            
            if len(self.users) > 0:
                st.success(
                    f"✅ {len(self.users)} user(s) loaded from secrets.toml: "
                    f"{', '.join(self.users.keys())}"
                )
            else:
                st.error("❌ No users configured. Please add [auth] section to secrets.toml")
            
            st.markdown("""
            **Security Notes:**
            - Passwords are stored in plain text in secrets.toml (keep file secure)
            - Use strong, unique passwords for each user
            - Never commit secrets.toml to version control
            - Consider using environment variables for production deployments
            """)
        
        return False
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        if not username or not password:
            return False
        
        if username not in self.users:
            return False
        
        stored_password = self.users[username]
        return self._verify_password(stored_password, password)
    
    def logout(self):
        """Clear authentication session"""
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.rerun()
    
    def show_user_info(self):
        """Display current user info and logout option with API key status"""
        if st.session_state.get('authenticated', False):
            username = st.session_state.get('username', 'Unknown')
            
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"👤 **Logged in as:** {username}")
                
                # Show API key configuration button for public users
                user_type = self.get_user_type(username)
                if user_type == 'public':
                    if st.button("🔑 Configure API Keys", use_container_width=True):
                        st.session_state['show_byok_setup'] = True
                        st.rerun()
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
                
                # Show API key status
                self.show_api_key_status(username)
    
    def require_auth(self, func):
        """Decorator to require authentication for a function"""
        def wrapper(*args, **kwargs):
            if self.login_form():
                return func(*args, **kwargs)
            else:
                st.stop()
        return wrapper

# Convenience function for quick setup
def init_auth() -> StreamlitAuth:
    """Initialize authentication system"""
    return StreamlitAuth()

def check_auth() -> bool:
    """Quick check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def protect_page(auth_system: StreamlitAuth):
    """Protect a page with authentication"""
    if not auth_system.login_form():
        st.stop()
    else:
        auth_system.show_user_info()