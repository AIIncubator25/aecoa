"""
UI Components for AECOA - Modular Interface Elements

🎨 Reusable UI components for clean separation of concerns
🔑 BYOK interface components
⚙️ Provider selection and configuration
📊 Status displays and validation feedback
"""

import streamlit as st
from typing import Dict, Optional
from .api_key_manager import api_key_manager

class BYOKInterface:
    """Bring Your Own Key interface components"""
    
    @staticmethod
    def render_byok_section(provider: str) -> bool:
        """
        Render BYOK input section for a specific provider
        Returns True if key was entered, False otherwise
        """
        if provider == "Ollama":
            st.info("🆓 Ollama runs locally and doesn't need an API key!")
            st.markdown("Make sure Ollama is running: `ollama serve`")
            return False
        
        # Provider-specific configuration
        config = BYOKInterface._get_provider_config(provider)
        
        user_key = st.text_input(
            f"{provider} API Key",
            type="password",
            placeholder=config["placeholder"],
            help=config["help_text"],
            key=f"user_api_key_input_{provider.lower()}"
        )
        
        if user_key:
            # Store the key
            api_key_manager.store_byok_key(provider, user_key)
            st.success(f"✅ {provider} API key configured")
            
            # Optional: Validate the key
            if st.button(f"🔍 Validate {provider} Key", key=f"validate_{provider.lower()}"):
                with st.spinner(f"Validating {provider} API key..."):
                    is_valid, message = api_key_manager.validate_api_key(provider, user_key)
                    if is_valid:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
            
            return True
        
        return False
    
    @staticmethod
    def _get_provider_config(provider: str) -> Dict[str, str]:
        """Get provider-specific configuration for UI"""
        configs = {
            "OpenAI": {
                "placeholder": "sk-your_openai_key_here",
                "help_text": "Get your API key from https://platform.openai.com/"
            },
            "GovTech": {
                "placeholder": "your_govtech_key_here", 
                "help_text": "Get your API key from GovTech AI services"
            }
        }
        return configs.get(provider, {"placeholder": "", "help_text": ""})


class ProviderStatusDisplay:
    """Display provider availability and configuration status"""
    
    @staticmethod
    def render_provider_status(username: str = None):
        """Render a status display for all providers"""
        providers = api_key_manager.get_available_providers(username)
        
        st.subheader("🔌 Provider Status")
        
        for provider, status in providers.items():
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col1:
                if status["available"]:
                    st.success(f"✅ {provider}")
                else:
                    st.error(f"❌ {provider}")
            
            with col2:
                source_icons = {
                    "byok": "🔑",
                    "admin": "🔐", 
                    "env": "🌐",
                    "none": "❓"
                }
                st.write(f"{source_icons[status['source']]} {status['source'].upper()}")
            
            with col3:
                if status["needs_byok"]:
                    st.warning("Needs BYOK")
                elif status["available"]:
                    st.info("Ready")
                else:
                    st.error("Not configured")


class CompactSidebar:
    """Compact sidebar components for better organization"""
    
    @staticmethod
    def render_ai_configuration():
        """Render AI provider configuration in sidebar"""
        st.header("🤖 AI Configuration")
        
        # Provider selection
        provider = st.selectbox(
            "AI Provider",
            ["OpenAI", "GovTech", "Ollama"],
            key="ai_provider"
        )
        
        # BYOK Section - Collapsible
        with st.expander("🔑 API Keys", expanded=False):
            username = st.session_state.get('username')
            providers_status = api_key_manager.get_available_providers(username)
            current_status = providers_status.get(provider, {})
            
            if current_status.get("available"):
                source = current_status["source"]
                if source == "byok":
                    st.success(f"✅ Using your {provider} key")
                elif source == "admin":
                    st.info(f"🔐 Using admin {provider} key")
                else:
                    st.info(f"🌐 Using environment {provider} key")
            else:
                st.warning(f"⚠️ {provider} not configured")
                BYOKInterface.render_byok_section(provider)
        
        return provider
    
    @staticmethod
    def render_model_selection(provider: str, use_dynamic_models: bool = True):
        """Render model selection based on provider"""
        if use_dynamic_models:
            # Import here to avoid circular imports
            try:
                from .model_manager import model_manager
                
                api_key = api_key_manager.get_api_key(
                    provider, 
                    st.session_state.get('username')
                )
                
                if api_key:
                    available_models = model_manager.get_models(provider)
                    if available_models:
                        default_model = CompactSidebar._get_default_model(provider)
                        
                        return st.selectbox(
                            "Model",
                            available_models,
                            index=(available_models.index(default_model) 
                                  if default_model in available_models else 0),
                            key="ai_model_select"
                        )
                
                # Fallback to text input
                return st.text_input(
                    "Model Name",
                    value=CompactSidebar._get_default_model(provider),
                    key="ai_model_text"
                )
            except ImportError:
                pass
        
        # Legacy text input mode
        return st.text_input(
            "Model Name",
            value=CompactSidebar._get_default_model(provider),
            key="ai_model"
        )
    
    @staticmethod
    def _get_default_model(provider: str) -> str:
        """Get default model for provider"""
        defaults = {
            "OpenAI": "gpt-4o-mini",
            "GovTech": "gpt-4o", 
            "Ollama": "llama3.2:latest"
        }
        return defaults.get(provider, "gpt-4o-mini")


class APITestInterface:
    """Interface for testing API connections"""
    
    @staticmethod
    def render_api_test_section():
        """Render API testing interface"""
        st.subheader("🧪 API Connection Test")
        
        username = st.session_state.get('username')
        providers = api_key_manager.get_available_providers(username)
        
        available_providers = [p for p, status in providers.items() if status["available"]]
        
        if not available_providers:
            st.warning("⚠️ No providers configured. Please add API keys above.")
            return
        
        test_provider = st.selectbox(
            "Test Provider",
            available_providers,
            key="test_provider_select"
        )
        
        if st.button(f"🔍 Test {test_provider} Connection"):
            with st.spinner(f"Testing {test_provider} connection..."):
                api_key = api_key_manager.get_api_key(test_provider, username)
                is_valid, message = api_key_manager.validate_api_key(test_provider, api_key)
                
                if is_valid:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")


# Convenience function for main app
def render_sidebar_ai_config():
    """Main function to render complete AI configuration sidebar"""
    provider = CompactSidebar.render_ai_configuration()
    st.markdown("---")
    model = CompactSidebar.render_model_selection(provider)
    st.markdown("---")
    APITestInterface.render_api_test_section()
    
    return provider, model