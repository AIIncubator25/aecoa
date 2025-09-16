"""
Simple Authentication System for Streamlit App
Protects API keys from unauthorized access
"""

import streamlit as st
import hashlib
import hmac
from typing import Dict, List

class StreamlitAuth:
    def __init__(self):
        self.users = self._load_users()
    
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
            return True
        
        # Create login form
        st.markdown("# 🔐 AEC Compliance Analysis - Login Required")
        st.markdown("Please log in to access the application and protect API resources.")
        
        with st.form("login_form"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown("### Please Enter Your Credentials")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit_button = st.form_submit_button("🚪 Login", use_container_width=True)
        
        # Handle login attempt
        if submit_button:
            if len(self.users) == 0:
                st.error("❌ No users configured in secrets.toml. Please check your configuration.")
                return False
            elif self.authenticate(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.success("✅ Login successful! Redirecting...")
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
                st.success(f"✅ {len(self.users)} user(s) loaded from secrets.toml: {', '.join(self.users.keys())}")
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
        """Display current user info and logout option"""
        if st.session_state.get('authenticated', False):
            username = st.session_state.get('username', 'Unknown')
            
            with st.sidebar:
                st.markdown("---")
                st.markdown(f"👤 **Logged in as:** {username}")
                
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()
    
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