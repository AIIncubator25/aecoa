"""
API Key Management System for AECOA

🔑 Handles both admin (pre-configured) and public (BYOK) API keys
🛡️ Secure storage, validation, and provider routing
🎯 Centralized API key logic for clean architecture
"""

import streamlit as st
import os
import requests
from typing import Dict, Optional, Tuple
import json

class APIKeyManager:
    """Centralized API key management for all providers"""
    
    def __init__(self):
        self.supported_providers = ["OpenAI", "GovTech", "Ollama"]
    
    def get_api_key(self, provider: str, username: str = None) -> Optional[str]:
        """
        Get API key for provider with security-focused hierarchy:
        1. User-provided BYOK key (session state) - for all users
        2. Admin pre-configured key (secrets.toml) - ADMIN ONLY
        3. Environment variable - fallback for local development
        
        SECURITY: Regular users MUST use BYOK, only admin can use secrets.toml
        """
        if provider not in self.supported_providers:
            return None
            
        # Check user-provided BYOK key first (available to all users)
        session_key = f"user_api_key_{provider.lower()}"
        if session_key in st.session_state and st.session_state[session_key]:
            return st.session_state[session_key]
        
        # Admin pre-configured keys - RESTRICTED TO ADMIN ONLY
        if self._is_admin_user(username):
            admin_key = self._get_admin_key(provider)
            if admin_key:
                return admin_key
        
        # Environment variables - fallback for local development only
        # Note: In production deployment, env vars should not contain API keys
        if self._is_local_development():
            return self._get_env_key(provider)
        
        # No API key available - user must provide BYOK
        return None
    
    def _is_local_development(self) -> bool:
        """Check if running in local development environment"""
        # This helps distinguish between local dev and production deployment
        try:
            # Check if we're running locally (not on Streamlit Cloud)
            import socket
            hostname = socket.gethostname()
            # Local development indicators
            local_indicators = ['localhost', 'local', 'dev', socket.gethostname()]
            return any(indicator in hostname.lower() for indicator in local_indicators)
        except:
            return False
    
    def _is_admin_user(self, username: str) -> bool:
        """Check if user has admin privileges for pre-configured keys"""
        if not username:
            return False
        admin_users = ['admin']  # Can be extended
        return username in admin_users
    
    def _get_admin_key(self, provider: str) -> Optional[str]:
        """Get pre-configured admin API key from secrets.toml - ADMIN ONLY"""
        try:
            if provider == "OpenAI":
                key = st.secrets.get("openai", {}).get("api_key")
                if key:
                    # Log admin key usage for security auditing
                    st.session_state.setdefault('admin_key_usage', []).append(f"Admin accessed {provider} key")
                return key
            elif provider == "GovTech":
                key = st.secrets.get("govtech", {}).get("api_key")
                if key:
                    st.session_state.setdefault('admin_key_usage', []).append(f"Admin accessed {provider} key")
                return key
        except Exception as e:
            # In production, secrets.toml might not exist - this is expected
            pass
        return None
    
    def _get_env_key(self, provider: str) -> Optional[str]:
        """Get API key from environment variables"""
        if provider == "OpenAI":
            return os.getenv("OPENAI_API_KEY")
        elif provider == "GovTech":
            return os.getenv("GOVTECH_API_KEY")
        return None
    
    def store_byok_key(self, provider: str, api_key: str) -> bool:
        """Store user-provided BYOK API key in session state"""
        if not provider or not api_key:
            return False
            
        session_key = f"user_api_key_{provider.lower()}"
        st.session_state[session_key] = api_key.strip()
        return True
    
    def validate_api_key(self, provider: str, api_key: str) -> Tuple[bool, str]:
        """Validate API key by testing connection"""
        if not api_key:
            return False, "No API key provided"
        
        try:
            if provider == "OpenAI":
                return self._test_openai_key(api_key)
            elif provider == "GovTech":
                return self._test_govtech_key(api_key)
            elif provider == "Ollama":
                return self._test_ollama_connection()
            else:
                return False, f"Unsupported provider: {provider}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _test_openai_key(self, api_key: str) -> Tuple[bool, str]:
        """Test OpenAI API key"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Simple test call to list models
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "OpenAI API key validated successfully"
            elif response.status_code == 401:
                return False, "Invalid OpenAI API key"
            else:
                return False, f"OpenAI API error: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"OpenAI connection error: {str(e)}"
    
    def _test_govtech_key(self, api_key: str) -> Tuple[bool, str]:
        """Test GovTech API key"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple completion request
            test_payload = {
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5,
                "temperature": 0
            }
            
            response = requests.post(
                "https://llmaas.govtext.gov.sg/gateway/openai/deployments/gpt-4/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, "GovTech API key validated successfully"
            elif response.status_code in [401, 403]:
                return False, "Invalid GovTech API key or insufficient permissions"
            else:
                return False, f"GovTech API error: {response.status_code}"
                
        except requests.RequestException as e:
            return False, f"GovTech connection error: {str(e)}"
    
    def _test_ollama_connection(self) -> Tuple[bool, str]:
        """Test Ollama local connection"""
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code == 200:
                return True, "Ollama connection successful"
            else:
                return False, f"Ollama connection failed: {response.status_code}"
        except requests.RequestException:
            return False, "Ollama not running on localhost:11434"
    
    def get_available_providers(self, username: str = None) -> Dict[str, dict]:
        """
        Get available providers with their status and BYOK requirements
        SECURITY: Emphasizes BYOK for regular users, admin access for pre-configured keys
        """
        providers = {}
        
        for provider in self.supported_providers:
            api_key = self.get_api_key(provider, username)
            has_key = bool(api_key)
            
            # Determine key source and requirements
            source = "none"
            requires_byok = True
            status_message = ""
            
            if has_key:
                session_key = f"user_api_key_{provider.lower()}"
                if session_key in st.session_state:
                    source = "byok"
                    requires_byok = False
                    status_message = "✅ Your API key (BYOK)"
                elif self._is_admin_user(username) and self._get_admin_key(provider):
                    source = "admin"
                    requires_byok = False
                    status_message = "🔐 Admin pre-configured"
                else:
                    source = "env"
                    requires_byok = False
                    status_message = "🛠️ Environment variable"
            else:
                if self._is_admin_user(username):
                    status_message = "⚠️ Configure in secrets.toml or use BYOK"
                elif provider == "Ollama":
                    requires_byok = False
                    status_message = "🏠 Local Ollama (no key needed)"
                else:
                    status_message = "🔑 Please provide your API key (BYOK required)"
            
            providers[provider] = {
                "available": has_key or (provider == "Ollama"),
                "source": source,
                "requires_byok": requires_byok,
                "status_message": status_message,
                "is_admin_accessible": self._is_admin_user(username)
            }
        
        return providers
    
    def clear_byok_keys(self):
        """Clear all BYOK keys from session state (e.g., on logout)"""
        for provider in self.supported_providers:
            session_key = f"user_api_key_{provider.lower()}"
            if session_key in st.session_state:
                del st.session_state[session_key]
        
        # Also clear input fields
        for provider in self.supported_providers:
            input_key = f"user_api_key_input_{provider.lower()}"
            if input_key in st.session_state:
                del st.session_state[input_key]


# Global instance
api_key_manager = APIKeyManager()