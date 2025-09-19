"""
AEC Compliance Analysis - Simplified Agentic Workflow
Main orchestration file for YAML-based compliance analysis using AI agents.

Workflow:
1. Step 1: Upload CSV/TXT/XLS → Convert to YAML + JSON with JsonLogic → Complete document processing
2. Step 2: Upload JPG/DXF → Analyze drawings → comparisons.csv (with compliance status)
3. Step 3: Generate executive report with insights and recommendations

All AI agents use the same provider/model selected in sidebar.
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Optional
import functools

# Enable caching and performance optimizations
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_json_file(file_path):
    """Cached JSON file loading."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data(ttl=1800)  # Cache for 30 minutes  
def get_file_summary_cached(file_names):
    """Cached file summary generation."""
    jpg_png_count = len([f for f in file_names if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    dxf_count = len([f for f in file_names if f.lower().endswith('.dxf')])
    return {
        'total_files': len(file_names),
        'image_files': jpg_png_count, 
        'dxf_files': dxf_count,
        'file_names': file_names
    }

# Import authentication system
from agents.auth.auth import StreamlitAuth

# Import core functionality
from agents.core.api_key_manager import api_key_manager

# Import our organized agents
from agents.parsers.agent1_unified_processor import UnifiedDocumentProcessor
from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent
from agents.reporters.agent3_combined_reporter import CombinedExecutiveReporter

# Import orchestrator for complex workflows
from agents.orchestrator import AgenticWorkflowOrchestrator

# --- Centralized Prompt Management ---
DEFAULT_PROMPTS = {
    "agent1_unified_processor": UnifiedDocumentProcessor.get_default_prompts(),
    "agent2_drawing_analyzer": DrawingAnalysisAgent.get_default_prompts(),
    "agent3_combined_reporter": CombinedExecutiveReporter.get_default_prompts()
}

def get_available_json_parameters():
    """Get list of available JSON parameter files from output folder."""
    try:
        output_dir = os.path.join(os.path.dirname(__file__), 'output', 'parameters')
        if not os.path.exists(output_dir):
            return []
        
        json_files = []
        for filename in os.listdir(output_dir):
            if filename.endswith('_parameters.json'):
                filepath = os.path.join(output_dir, filename)
                # Get file modification time for sorting (newest first)
                mtime = os.path.getmtime(filepath)
                json_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'display_name': filename.replace('_parameters.json', ''),
                    'mtime': mtime
                })
        
        # Sort by modification time (newest first)
        json_files.sort(key=lambda x: x['mtime'], reverse=True)
        return json_files
    except Exception as e:
        st.error(f"Error reading JSON parameter files: {e}")
        return []

def get_agent_prompts():
    """Get current agent prompts from session state or defaults."""
    if 'agent_prompts' not in st.session_state:
        st.session_state.agent_prompts = DEFAULT_PROMPTS.copy()
    return st.session_state.agent_prompts

def update_agent_prompt(agent_name: str, prompt_type: str, new_prompt: str):
    """Update a specific agent prompt."""
    prompts = get_agent_prompts()
    if agent_name not in prompts:
        prompts[agent_name] = {}
    prompts[agent_name][prompt_type] = new_prompt
    st.session_state.agent_prompts = prompts

def render_prompt_editor():
    """Render the prompt editor UI."""
    st.header("🎛️ AI Agent Prompt Management")
    st.markdown("*View and customize the AI prompts used by each agent*")
    
    prompts = get_agent_prompts()
    
    for agent_name, agent_prompts in prompts.items():
        # Map agent names to step names for better UX
        step_mapping = {
            "agent1_unified_processor": "Step 1 - Document Processing",
            "agent2_drawing_analyzer": "Step 2 - Drawing Analysis Agent", 
            "agent3_combined_reporter": "Step 3 - Executive Report & Insights Generator"
        }
        agent_display_name = step_mapping.get(agent_name, agent_name.replace('_', ' ').title())
        
        with st.expander(f"🤖 {agent_display_name}", expanded=False):
            st.markdown(f"**Agent:** `{agent_name}`")
            
            # System prompt editor
            if 'system' in agent_prompts:
                st.markdown("**System Prompt:**")
                new_system = st.text_area(
                    "System instructions",
                    value=agent_prompts['system'],
                    height=100,
                    key=f"{agent_name}_system",
                    help="Core instructions that define the agent's role and capabilities"
                )
                if new_system != agent_prompts['system']:
                    update_agent_prompt(agent_name, 'system', new_system)
                    st.success(f"Updated {agent_display_name} system prompt")
            
            # User prompt editor
            if 'user' in agent_prompts:
                st.markdown("**User Prompt Template:**")
                new_user = st.text_area(
                    "Task instructions",
                    value=agent_prompts['user'],
                    height=200,
                    key=f"{agent_name}_user",
                    help="Specific task instructions with placeholders for dynamic content"
                )
                if new_user != agent_prompts['user']:
                    update_agent_prompt(agent_name, 'user', new_user)
                    st.success(f"Updated {agent_display_name} user prompt")
            
            # Reset to default button
            if st.button(f"🔄 Reset {agent_display_name} to Default", key=f"reset_{agent_name}"):
                if agent_name in DEFAULT_PROMPTS:
                    st.session_state.agent_prompts[agent_name] = DEFAULT_PROMPTS[agent_name].copy()
                    st.success(f"Reset {agent_display_name} prompts to default")
                    st.rerun()
    
    # Export/Import prompts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export All Prompts", use_container_width=True):
            import json
            prompts_json = json.dumps(prompts, indent=2)
            st.download_button(
                "Download prompts.json",
                prompts_json,
                "agent_prompts.json",
                "application/json",
                use_container_width=True
            )
    
    with col2:
        uploaded_prompts = st.file_uploader("📤 Import Prompts", type=['json'])
        if uploaded_prompts:
            try:
                import json
                new_prompts = json.load(uploaded_prompts)
                st.session_state.agent_prompts = new_prompts
                st.success("Prompts imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to import prompts: {str(e)}")

def initialize_session():
    """Initialize session state variables."""
    if 'step1_completed' not in st.session_state:
        st.session_state.step1_completed = False
        st.session_state.parameters_df = None
        st.session_state.step2_completed = False
        st.session_state.comparisons_df = None
        st.session_state.step3_completed = False
        st.session_state.executive_report = None

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for the selected provider using the centralized manager."""
    username = st.session_state.get('username')
    return api_key_manager.get_api_key(provider, username)

def main():
    # Page config
    st.set_page_config(
        page_title="AEC Compliance Checks",
        page_icon="🏗️",
        layout="wide"
    )
    
    # Initialize authentication
    from agents.auth import StreamlitAuth
    auth = StreamlitAuth()
    
    # Check authentication
    if not st.session_state.get('authenticated', False):
        # Show login form
        st.title("🔐 Login Required")
        st.markdown("Please login to access the AEC Compliance Analysis system.")
        st.markdown("---")
        
        if auth.login_form():
            st.rerun()  # Refresh after successful login
        return  # Stop here if not authenticated
    
    # Show user info and logout option in sidebar after authentication
    with st.sidebar:
        auth.show_user_info()
        st.markdown("---")
    
    # Initialize session
    initialize_session()
    
    # Header
    st.title("🏗️ AEC Compliance Analysis")
    st.markdown("*Automated compliance checking using AI agents for YAML requirements and technical drawings*")
    
    # Main navigation tabs
    tab1, tab2 = st.tabs(["📋 Compliance Workflow", "🎛️ Prompt Management"])
    
    with tab2:
        render_prompt_editor()
    
    with tab1:
        # Continue with the main workflow...
        # Sidebar for AI Agent Configuration
        with st.sidebar:
            st.header("🤖 AI Agent Configuration")
            st.markdown("*Select AI provider and model for all agents*")
            
            # Import model manager
            try:
                from agents.model_manager import model_manager
                use_dynamic_models = True
            except ImportError:
                st.warning("Model manager not available, using legacy mode")
                use_dynamic_models = False
            
            provider = st.selectbox(
                "AI Provider",
                ["OpenAI", "GovTech", "Ollama"],
                key="ai_provider"
            )
            
            # Get current user info
            username = st.session_state.get('username', '')
            is_admin = username == 'admin'
            
            # API Key Status & BYOK Interface
            st.markdown("---")
            
            # Show different interfaces for admin vs regular users
            if is_admin:
                st.markdown("**🔐 Admin Key Management**")
                with st.expander("ℹ️ Admin Key Sources", expanded=False):
                    st.info("""
                    **Admin users can use:**
                    • 🔑 **BYOK**: Your own API keys (recommended)
                    • 🔐 **Pre-configured**: Keys from secrets.toml (local only)
                    
                    *BYOK provides better security and cost control*
                    """)
            else:
                st.markdown("**🔑 API Key Required (BYOK)**")
                st.info("**Regular users must provide their own API keys for security**")
            
            # BYOK Interface for all users
            byok_expanded = not is_admin or not api_key_manager.get_api_key(provider, username)
            with st.expander("🔑 Bring Your Own API Key (BYOK)", expanded=byok_expanded):
                st.markdown("**Secure API key management:**")
                st.markdown("✅ Keys stored in session only • ✅ Never logged or saved • ✅ Full cost control")
                
                if provider == "OpenAI":
                    user_key = st.text_input(
                        "OpenAI API Key",
                        type="password",
                        placeholder="sk-your_openai_key_here",
                        help="Get your API key from https://platform.openai.com/",
                        key=f"user_api_key_input_{provider.lower()}"
                    )
                    if user_key:
                        st.session_state[f"user_api_key_{provider.lower()}"] = user_key
                        st.success("✅ OpenAI API key configured securely")
                
                elif provider == "GovTech":
                    user_key = st.text_input(
                        "GovTech API Key",
                        type="password",
                        placeholder="your_govtech_key_here",
                        help="Get your API key from GovTech AI services",
                        key=f"user_api_key_input_{provider.lower()}"
                    )
                    if user_key:
                        st.session_state[f"user_api_key_{provider.lower()}"] = user_key
                        st.success("✅ GovTech API key configured securely")
                
                elif provider == "Ollama":
                    st.success("🆓 Ollama runs locally and doesn't need an API key!")
                    st.markdown("**Setup:** Make sure Ollama is running locally: `ollama serve`")
                    
            # Show current key status
            current_key = api_key_manager.get_api_key(provider, username)
            if current_key:
                providers_status = api_key_manager.get_available_providers(username)
                status_info = providers_status.get(provider, {})
                st.success(f"🔑 {provider}: {status_info.get('status_message', 'Ready')}")
            elif provider != "Ollama":
                if is_admin:
                    st.warning(f"⚠️ {provider}: Configure key in secrets.toml or use BYOK above")
                else:
                    st.error(f"❌ {provider}: Please provide your API key using BYOK above")
            
            st.markdown("---")
            
            # Dynamic model selection
            if use_dynamic_models:
                # Get available models for selected provider
                api_key = get_api_key(provider)
                available_models = {}
                
                try:
                    if provider == "OpenAI":
                        available_models = model_manager.get_openai_models(api_key)
                    elif provider == "GovTech":
                        available_models = model_manager.get_govtech_models(api_key)
                    elif provider == "Ollama":
                        available_models = model_manager.get_ollama_models()
                except Exception as e:
                    st.error(f"Error loading models: {e}")
                
                if available_models:
                    # Show model selectbox with descriptions
                    model_options = list(available_models.keys())
                    
                    # Get default model based on provider
                    if provider == "OpenAI":
                        default_model = "gpt-4o-mini"
                    elif provider == "GovTech":
                        default_model = "gpt-4o"
                    elif provider == "Ollama":
                        default_model = "llava:latest"
                    else:
                        default_model = "gpt-4o"
                    
                    if default_model not in model_options and model_options:
                        default_model = model_options[0]
                    
                    selected_model = st.selectbox(
                        "Model",
                        model_options,
                        index=model_options.index(default_model) if default_model in model_options else 0,
                        key=f"ai_model_select_{provider}"
                    )
                    
                    # Show model information
                    if selected_model in available_models:
                        model_info = available_models[selected_model]
                        st.info(f"""
                        **{model_info.name}**
                        
                        {model_info.description}
                        
                        • Context: {model_info.context_length:,} tokens
                        • Vision: {'✅' if model_info.supports_vision else '❌'}
                        • Cost: {'Free' if model_info.cost_per_1k_tokens == 0 else f'${model_info.cost_per_1k_tokens}/1K tokens' if model_info.cost_per_1k_tokens else 'N/A'}
                        
                        **Recommended for:** {', '.join(model_info.recommended_for or [])}
                        """)
                    
                    model = selected_model
                    st.session_state.ai_model = selected_model  # Store in session state
                else:
                    # Fallback to text input if no models detected
                    model = st.text_input(
                        "Model Name",
                        value="gpt-4o-mini" if provider == "OpenAI" else "gpt-4o",
                        key="ai_model_text",
                        help="Enter model name manually"
                    )
                    st.session_state.ai_model = model  # Store in session state
            else:
                # Legacy text input mode
                model = st.text_input(
                    "Model Name",
                    value="gpt-4o-mini" if provider == "OpenAI" else "gpt-4",
                    key="ai_model"
                )
                st.session_state.ai_model = model  # Store in session state
            
            # Get API key
            api_key = get_api_key(provider)
            
            # Display API key status with enhanced debugging
            if provider in ["OpenAI", "GovTech"]:
                if api_key:
                    # Mask the API key for security (show first 7 and last 4 characters)
                    masked_key = f"{api_key[:7]}...{api_key[-4:]}" if len(api_key) > 15 else "***masked***"
                    st.success(f"✅ {provider} API key configured")
                    st.code(f"Key: {masked_key}", language=None)
                    
                    # Test API key button
                    if st.button(f"🧪 Test {provider} API Key", key=f"test_api_{provider}"):
                        with st.spinner(f"Testing {provider} API connection..."):
                            try:
                                # Simple test API call
                                import requests
                                if provider == "OpenAI":
                                    url = "https://api.openai.com/v1/models"
                                    headers = {"Authorization": f"Bearer {api_key}"}
                                    response = requests.get(url, headers=headers, timeout=10)
                                    if response.status_code == 200:
                                        st.success("✅ API key is valid and working!")
                                    else:
                                        st.error(f"❌ API test failed: {response.status_code} - {response.text}")
                                elif provider == "GovTech":
                                    # Test GovTech API using chat completions endpoint
                                    url = "https://llmaas.govtext.gov.sg/gateway/openai/deployments/gpt-4/chat/completions"
                                    headers = {
                                        "api-key": api_key,
                                        "Content-Type": "application/json"
                                    }
                                    test_payload = {
                                        "messages": [{"role": "user", "content": "Hello"}],
                                        "max_tokens": 5,
                                        "temperature": 0.0
                                    }
                                    response = requests.post(url, headers=headers, json=test_payload, timeout=30)
                                    if response.status_code == 200:
                                        st.success("✅ GovTech API key is valid and working!")
                                    elif response.status_code == 401:
                                        st.error("❌ Invalid GovTech API key")
                                    elif response.status_code == 403:
                                        st.error("❌ GovTech API key lacks permissions")
                                    elif response.status_code == 429:
                                        st.error("❌ GovTech API rate limit exceeded")
                                    else:
                                        try:
                                            error_info = response.json() if response.text else {}
                                            error_msg = error_info.get('error', {}).get('message', response.text[:200])
                                            st.error(f"❌ GovTech API error ({response.status_code}): {error_msg}")
                                        except:
                                            st.error(f"❌ GovTech API error: {response.status_code} - {response.text[:200]}")
                            except Exception as e:
                                st.error(f"❌ API test error: {str(e)}")
                else:
                    st.error(f"❌ {provider} API key not found")
                    st.info("**How to fix:**")
                    st.code(f"""
# Option 1: Add to .streamlit/secrets.toml
[{provider.lower()}]
api_key = "your-api-key-here"

# Option 2: Set environment variable
export {provider.upper()}_API_KEY="your-api-key-here"
                    """)
                    st.warning("⚠️ Step 1 will not work without a valid API key")
            else:
                st.info("📝 Ollama: Local model (configure endpoint if needed)")
            
            # Agent status
            st.markdown("### 🔄 Agent Status")
            st.markdown(f"**Step 1**: Document Processing (YAML + JSON)")
            st.markdown(f"**Step 2**: Drawing Analysis Agent")
            st.markdown(f"**Step 3**: Executive Report & Insights Generator")
            st.markdown(f"**Provider**: {provider}")
            st.markdown(f"**Model**: {model}")
        
        # Main workflow
        st.header("📋 Compliance Analysis Workflow")
        
        # Step 1: Unified Document Processing (CSV → YAML + JSON with JsonLogic)
        step1_processor = UnifiedDocumentProcessor(provider=provider, model=model)
        step1_processor.render_step1_ui()
        
        # Step 2: Drawing Analysis
        st.markdown("---")
        st.subheader("Step 2: Upload Technical Drawings")
        st.markdown("*Upload JPG/PNG/DXF files for compliance analysis against extracted parameters*")
        
        # JSON Parameter Selection
        available_json = get_available_json_parameters()
        selected_json = None
        
        # Step 2: Drawing Analysis with flexible JSON parameter options
        if available_json or True:  # Always show Step 2 options
            st.markdown("### 📋 Parameter Requirements Source")
            
            # Option 1: Select from Step 1 generated files
            param_source = st.radio(
                "Choose how to provide requirement parameters:",
                ["Use JSON from Step 1 (Agent 1)", "Upload custom JSON file", "Provide JSON file path"],
                key="param_source_option"
            )
            
            selected_json = None
            
            if param_source == "Use JSON from Step 1 (Agent 1)":
                if available_json:
                    st.markdown("**📋 Select Parameters File from Step 1:**")
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        json_options = [f"{item['display_name']} ({item['filename']})" for item in available_json]
                        selected_idx = st.selectbox(
                            "Choose JSON parameters from Step 1 (Agent 1):",
                            range(len(json_options)),
                            format_func=lambda i: json_options[i],
                            key="json_selector"
                        )
                        selected_json = available_json[selected_idx]['filepath']
                    
                    with col2:
                        st.metric("Available Files", len(available_json))
                        
                else:
                    st.warning("⚠️ No JSON parameter files found. Complete Step 1 (Agent 1) first to generate parameters.")
                    st.info("💡 JSON parameters are automatically saved to `output/parameters/` when you process documents in Step 1.")
            
            elif param_source == "Upload custom JSON file":
                uploaded_json = st.file_uploader(
                    "Upload your custom JSON parameters file:",
                    type=['json'],
                    key="custom_json_uploader",
                    help="Upload a JSON file with parameter templates for compliance analysis"
                )
                
                if uploaded_json:
                    # Save uploaded file temporarily
                    temp_json_path = os.path.join("output", "parameters", f"custom_{uploaded_json.name}")
                    os.makedirs(os.path.dirname(temp_json_path), exist_ok=True)
                    
                    with open(temp_json_path, "wb") as f:
                        f.write(uploaded_json.getvalue())
                    
                    selected_json = temp_json_path
                    st.success(f"✅ Custom JSON file uploaded: {uploaded_json.name}")
                    
            elif param_source == "Provide JSON file path":
                custom_path = st.text_input(
                    "Enter full path to JSON parameters file:",
                    placeholder="C:\\path\\to\\your\\parameters.json",
                    key="custom_json_path"
                )
                
                if custom_path and os.path.exists(custom_path):
                    selected_json = custom_path
                    st.success(f"✅ JSON file found: {custom_path}")
                elif custom_path:
                    st.error(f"❌ File not found: {custom_path}")
            
            # Show JSON file location and allow editing
            if selected_json:
                st.markdown("### 📄 Current Requirements File")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.code(f"📍 Location: {selected_json}", language="text")
                    
                with col2:
                    if st.button("📝 View/Edit JSON", key="view_edit_json"):
                        st.session_state['show_json_editor'] = True
                
                # JSON Editor
                if st.session_state.get('show_json_editor', False):
                    with st.expander("📝 JSON Parameters Editor", expanded=True):
                        try:
                            with open(selected_json, 'r', encoding='utf-8') as f:
                                json_content = f.read()
                            
                            edited_json = st.text_area(
                                "Edit JSON parameters (changes will be saved when you click Save):",
                                value=json_content,
                                height=300,
                                key="json_editor"
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("💾 Save Changes", key="save_json"):
                                    try:
                                        # Validate JSON
                                        json.loads(edited_json)
                                        
                                        # Save changes
                                        with open(selected_json, 'w', encoding='utf-8') as f:
                                            f.write(edited_json)
                                        
                                        st.success("✅ JSON file updated successfully!")
                                    except json.JSONDecodeError as e:
                                        st.error(f"❌ Invalid JSON format: {e}")
                                        
                            with col2:
                                if st.button("❌ Close Editor", key="close_json_editor"):
                                    st.session_state['show_json_editor'] = False
                                    st.rerun()
                                    
                        except Exception as e:
                            st.error(f"❌ Error reading JSON file: {e}")
        else:
            st.warning("⚠️ No JSON parameter files found. Complete Step 1 first to generate parameters.")
            st.info("💡 JSON parameters are automatically saved to the output folder when you process documents in Step 1.")
        
        ### 🖼️ Drawing Files Upload
        st.markdown("### 🖼️ Upload Drawing Files")
        drawing_files = st.file_uploader(
            "Choose drawing files (JPG, PNG, DXF)",
            type=['jpg', 'jpeg', 'png', 'dxf'],
            accept_multiple_files=True,
            key="drawing_uploader",
            help="Upload technical drawings: floor plans, elevations, sections, details, schedules, diagrams"
        )
        
        # Custom prompt upload option
        st.markdown("### 🔧 Analysis Configuration")
        with st.expander("🧠 AI Analysis Settings", expanded=True):
            
            # Analysis mode selection
            analysis_mode = st.radio(
                "🎯 Choose Analysis Approach:",
                [
                    "🧠 Intelligent AI Analysis (Recommended)", 
                    "📊 Structured JSON Analysis",
                    "🎨 Custom Prompts"
                ],
                help="Intelligent mode uses AI's natural understanding. JSON mode uses structured parsing. Custom allows full customization.",
                key="analysis_mode"
            )
            
            if analysis_mode == "🧠 Intelligent AI Analysis (Recommended)":
                st.info("✨ **AI-Driven Approach**: Leverages AI's intelligence to understand drawings and requirements naturally. AI focuses on visual interpretation and contextual understanding rather than rigid parsing rules.")
                
            elif analysis_mode == "📊 Structured JSON Analysis":
                st.info("🔧 **Structured Approach**: Uses predefined JSON schemas for consistent output formatting. More rigid but predictable.")
                
            elif analysis_mode == "🎨 Custom Prompts":
                st.markdown("**Upload custom prompts to tailor the AI analysis for specific requirements:**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    custom_system_prompt = st.file_uploader(
                        "System Prompt File (.txt)",
                        type=['txt'],
                        key="custom_system_prompt",
                        help="Custom system instructions for the AI analyst"
                    )
                
                with col2:
                    custom_user_prompt = st.file_uploader(
                        "User Prompt Template (.txt)", 
                        type=['txt'],
                        key="custom_user_prompt",
                        help="Custom task template with requirement details"
                    )
                
                with col3:
                    custom_output_format = st.file_uploader(
                        "Output Format Template (.txt/.csv)",
                        type=['txt', 'csv'],
                        key="custom_output_format",
                        help="Custom output format specification or example CSV structure"
                    )
                
                # Custom output format specification
                st.markdown("**📊 Custom Output Format (Optional):**")
                output_format_option = st.radio(
                    "Choose output format customization:",
                    ["Use default format", "Upload format template", "Define custom format inline"],
                    key="output_format_option"
                )
                
                custom_format_text = ""
                if output_format_option == "Define custom format inline":
                    custom_format_text = st.text_area(
                        "Define your desired output format:",
                        placeholder="""Example format instructions:
- Use table format with columns: No, Clause, Parameter, Required Value, Found Value, Compliance, Reference
- Include header row with requirements and identified values sections
- Add compliance status as Y/N instead of Compliant/Non-Compliant
- Include specific drawing reference for each parameter""",
                        height=150,
                        key="custom_format_inline"
                    )
                
                if custom_system_prompt or custom_user_prompt or custom_output_format or custom_format_text:
                    st.info("💡 Custom prompts and formats will override default analysis instructions")
        
        if drawing_files and selected_json:
            # Initialize Agent 2 for file processing
            agent2 = DrawingAnalysisAgent(provider=provider, model=model)
            file_summary = agent2.get_file_summary(drawing_files)
            
            # Validate requirements JSON (preview UI removed by request)
            try:
                with open(selected_json, 'r', encoding='utf-8') as f:
                    _ = json.load(f)
            except Exception as e:
                st.error(f"❌ Error reading JSON requirements: {e}")
                return
            
            if file_summary['dxf_files'] > 0:
                # Check if DXF text extraction is available
                try:
                    from agents.analyzers.file_handler import DXF_AVAILABLE
                    if DXF_AVAILABLE:
                        st.success(f"✅ {file_summary['dxf_files']} DXF file(s) detected - Text extraction enabled for comprehensive analysis")
                        st.info("💡 DXF files will be processed to extract text, dimensions, and table data for AI analysis")
                    else:
                        st.warning("⚠️ DXF files detected but ezdxf library not available - Install ezdxf for enhanced DXF text extraction")
                except ImportError:
                    st.warning("⚠️ DXF files will be saved but text extraction is limited - JPG/PNG recommended for best AI analysis")
            
            # Analysis button with enhanced functionality
            if st.button("🔍 Analyze Drawings for Compliance", key="analyze_drawings", use_container_width=True):
                with st.spinner("🤖 Agent 2: Analyzing drawings against requirements..."):
                    # Initialize Agent 2 with selected configuration
                    agent2 = DrawingAnalysisAgent(provider=provider, model=model)
                    
                    # Configure analysis mode
                    if analysis_mode == "🧠 Intelligent AI Analysis (Recommended)":
                        agent2.set_intelligent_mode(True)
                        st.info("🧠 Using intelligent AI analysis approach")
                        
                    elif analysis_mode == "🎨 Custom Prompts":
                        # Handle custom prompts
                        prompts = get_agent_prompts()
                        
                        # Load custom prompts if provided
                        if custom_system_prompt:
                            custom_sys_content = custom_system_prompt.read().decode('utf-8')
                            prompts['agent2_drawing_analyzer']['system'] = custom_sys_content
                            st.info("✅ Using custom system prompt")
                        
                        if custom_user_prompt:
                            custom_user_content = custom_user_prompt.read().decode('utf-8')
                            prompts['agent2_drawing_analyzer']['user'] = custom_user_content
                            st.info("✅ Using custom user prompt")
                        
                        # Process custom output format
                        custom_output_instructions = ""
                        if custom_output_format:
                            format_content = custom_output_format.read().decode('utf-8')
                            if custom_output_format.name.endswith('.csv'):
                                custom_output_instructions = f"""
**CUSTOM OUTPUT FORMAT (CSV Example Provided):**
Follow this exact CSV structure:
```
{format_content}
```
Generate output that matches this format exactly, including headers and column structure.
"""
                            else:
                                custom_output_instructions = f"""
**CUSTOM OUTPUT FORMAT INSTRUCTIONS:**
{format_content}
"""
                            st.info("✅ Using custom output format template")
                        elif output_format_option == "Define custom format inline" and custom_format_text:
                            custom_output_instructions = f"""
**CUSTOM OUTPUT FORMAT REQUIREMENTS:**
{custom_format_text}

Follow these specific formatting requirements exactly.
"""
                            st.info("✅ Using custom inline format definition")
                        
                        # Enhance prompts with detailed requirements context
                        requirements_context = f"""
**DETAILED REQUIREMENTS FROM JSON ({os.path.basename(selected_json)}):**

{json.dumps(param_templates, indent=2, ensure_ascii=False, separators=(',', ': '))}

**ANALYSIS TASK:**
Create a comprehensive comparison table showing:
1. **Requirements columns:** No, Clause, Parameter, Min. Rectilinear HS Countable Area, Min. Irregular HS Countable Area, Unit, Min. Volume (m3)
2. **Identified Values columns:** Unit Area, HS Area, HS Volume, HS Slab Thickness, HS underneath Staircase Waist Thickness, Compliance (Y/N), Reference Drawing

Map each requirement to identified values from the drawings, providing specific compliance status and source references.

{custom_output_instructions}

**IMPORTANT:** Return ONLY a valid JSON response. Do not include any explanatory text, markdown formatting, or code blocks.
"""
                        
                        # Inject requirements into user prompt
                        if '{param_context}' in prompts['agent2_drawing_analyzer']['user']:
                            prompts['agent2_drawing_analyzer']['user'] = prompts['agent2_drawing_analyzer']['user'].replace(
                                '{param_context}', requirements_context
                            )
                        
                        # Set enhanced prompts
                        if hasattr(agent2, 'set_prompts'):
                            agent2.set_prompts(prompts['agent2_drawing_analyzer'])
                    
                    else:  # Structured JSON Analysis
                        # Use default structured approach
                        prompts = get_agent_prompts()
                        requirements_context = f"""
**DETAILED REQUIREMENTS FROM JSON ({os.path.basename(selected_json)}):**

{json.dumps(param_templates, indent=2, ensure_ascii=False, separators=(',', ': '))}

**ANALYSIS TASK:**
Create a comprehensive comparison table showing:
1. **Requirements columns:** No, Clause, Parameter, Min. Rectilinear HS Countable Area, Min. Irregular HS Countable Area, Unit, Min. Volume (m3)
2. **Identified Values columns:** Unit Area, HS Area, HS Volume, HS Slab Thickness, HS underneath Staircase Waist Thickness, Compliance (Y/N), Reference Drawing

Map each requirement to identified values from the drawings, providing specific compliance status and source references.

**IMPORTANT:** Return ONLY a valid JSON response. Do not include any explanatory text, markdown formatting, or code blocks.
"""
                        
                        if '{param_context}' in prompts['agent2_drawing_analyzer']['user']:
                            prompts['agent2_drawing_analyzer']['user'] = prompts['agent2_drawing_analyzer']['user'].replace(
                                '{param_context}', requirements_context
                            )
                        
                        if hasattr(agent2, 'set_prompts'):
                            agent2.set_prompts(prompts['agent2_drawing_analyzer'])
                    
                    # Process drawings using JSON parameters file
                    processing_result = agent2.process_drawing_files(drawing_files, selected_json, api_key)
                    
                    if processing_result['analysis_success']:
                        analysis_result = processing_result['analysis_result']
                        st.session_state.comparisons_df = analysis_result['comparisons_df']
                        st.session_state.step2_completed = True
                        
                        # Save analysis results to output folder
                        try:
                            output_dir = os.path.join(os.path.dirname(__file__), 'output', 'analysis')
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # Save comparisons CSV
                            param_name = os.path.basename(selected_json).replace('_parameters.json', '')
                            results_filename = f"{param_name}_drawing_analysis.csv"
                            results_filepath = os.path.join(output_dir, results_filename)
                            analysis_result['comparisons_df'].to_csv(results_filepath, index=False)
                            
                            st.success(f"✅ Drawing analysis completed using {analysis_result.get('method', 'Unknown')} method")
                            st.info(f"📁 Results saved to: {results_filename}")
                        except Exception as save_error:
                            st.warning(f"⚠️ Could not save analysis results: {save_error}")
                        
                        st.info(analysis_result.get('info', ''))
                        
                        # Show drawing titles if available
                        if 'drawing_titles' in analysis_result and analysis_result['drawing_titles']:
                            st.markdown("**📋 Identified Drawing Titles:**")
                            for title in analysis_result['drawing_titles']:
                                st.markdown(f"- {title}")
                    else:
                        st.error(f"❌ Drawing analysis failed: {processing_result.get('error')}")
        elif drawing_files and not selected_json:
            # Allow direct JPG processing with full 2.10 HS parameters if available
            full_params_json = os.path.join(os.path.dirname(__file__), 'output', 'parameters', '2.10_HS_parameters.json')
            default_params_csv = "hs_parameters.csv"
            
            if os.path.exists(full_params_json):
                st.info("💡 **Enhanced Processing Mode**: Using complete 2.10 HS parameters for comprehensive analysis")
                parameters_file = full_params_json
                
                # Validate full parameters JSON (preview UI removed by request)
                try:
                    with open(full_params_json, 'r', encoding='utf-8') as f:
                        _ = json.load(f)
                except Exception as e:
                    st.warning(f"Could not load full parameters: {e}. Using default parameters.")
                    parameters_file = default_params_csv
                    st.info("💡 **Direct Processing Mode**: Using default HS parameters for analysis")
            else:
                st.info("💡 **Direct Processing Mode**: Using default HS parameters for analysis")
                parameters_file = default_params_csv
            
            # Show option to proceed with analysis
            if st.button("🚀 Analyze with HS Parameters", key="direct_analyze", use_container_width=True):
                with st.spinner("🤖 Agent 2: Analyzing drawings with HS parameters..."):
                    # Initialize Agent 2
                    agent2 = DrawingAnalysisAgent(provider=provider, model=model)
                    
                    if analysis_mode == "🧠 Intelligent AI Analysis (Recommended)":
                        agent2.set_intelligent_mode(True)
                        st.info("🧠 Using intelligent AI analysis approach")
                    
                    # Process drawings with HS parameters
                    processing_result = agent2.process_drawing_files(drawing_files, parameters_file, api_key)
                    
                    if processing_result['analysis_success']:
                        analysis_result = processing_result['analysis_result']
                        st.session_state.comparisons_df = analysis_result['comparisons_df']
                        st.session_state.step2_completed = True
                        
                        # Save analysis results
                        try:
                            output_dir = os.path.join(os.path.dirname(__file__), 'output', 'analysis')
                            os.makedirs(output_dir, exist_ok=True)
                            
                            # Save comparisons CSV
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            results_filename = f"hs_drawing_analysis_{timestamp}.csv"
                            results_filepath = os.path.join(output_dir, results_filename)
                            analysis_result['comparisons_df'].to_csv(results_filepath, index=False)
                            
                            st.success(f"✅ Drawing analysis completed using {analysis_result.get('method', 'AI Analysis')} method")
                            st.info(f"📁 Results saved to: {results_filename}")
                            
                            # Show file summary
                            file_summary = agent2.get_file_summary(drawing_files)
                            st.info(f"📁 Processed: {file_summary['image_files']} images, {file_summary['dxf_files']} DXF files")
                            
                        except Exception as save_error:
                            st.warning(f"⚠️ Could not save analysis results: {save_error}")
                        
                        st.info(analysis_result.get('info', 'Analysis completed successfully'))
                        
                    else:
                        st.error(f"❌ Drawing analysis failed: {processing_result.get('error')}")
            
            # Show parameters being used
            if os.path.exists(full_params_json):
                st.markdown("**📋 Complete 2.10 HS Requirements Being Used:**")
                st.info("""
                ✅ **Comprehensive Analysis Including:**
                - **HS Minimum Area Requirements** (5 GFA-based tiers: 1.44-3.4 m²)
                - HS Volume calculations (3.6-9.0 m³)
                - Height Clearance Requirements (≥1500mm)
                - **HS Ceiling Slab Thickness (≥300mm)** 
                - **Waist of Staircase Thickness (≥300mm)** ⭐
                - **HS Wall Thickness (≥200mm)** 🧱
                - Ventilation Sleeve Wall Clearance (≥700mm)
                - GFA-based compliance validation
                - Complete structural adequacy matrix
                """)
            else:
                st.markdown("**📋 Default HS Parameters Being Used:**")
                st.info("""
                - HS Floor Area (clear height ≥ 1500mm): 2.20 m²
                - HS Enclosed Volume: 5.4 m³  
                - HS Ceiling Slab Thickness: 300 mm
                - **Waist of Staircase Thickness: 300 mm** ⭐
                - Ventilation Sleeve Wall Clearance: 700 mm
                """)
        else:
            st.warning("⚠️ Please upload JPG/DXF files to proceed with analysis.")
    
        # Display compliance comparison if Step 2 completed
        if st.session_state.step2_completed and st.session_state.comparisons_df is not None:
            st.markdown("---")
            st.subheader("� Requirements vs Identified Values Analysis")
            
            # Get compliance metrics using agent method
            agent2 = DrawingAnalysisAgent()
            metrics = agent2.get_compliance_metrics(st.session_state.comparisons_df)
            
            # Enhanced metrics display
            st.markdown("### 📈 Compliance Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Parameters", metrics['total_parameters'])
            with col2:
                compliant_color = "normal" if metrics['compliant'] > 0 else "off"
                st.metric("✅ Compliant", metrics['compliant'], 
                         delta=f"{metrics['compliance_rate']:.1f}%", 
                         delta_color=compliant_color)
            with col3:
                non_compliant_color = "inverse" if metrics['non_compliant'] > 0 else "off"
                st.metric("❌ Non-Compliant", metrics['non_compliant'], 
                         delta=f"{metrics['non_compliance_rate']:.1f}%", 
                         delta_color=non_compliant_color)
            with col4:
                not_found_color = "inverse" if metrics['not_found'] > 0 else "off"
                st.metric("❓ Not Found", metrics['not_found'], 
                         delta=f"{metrics['not_found_rate']:.1f}%", 
                         delta_color=not_found_color)
            
            # Compliance status indicator
            if metrics['compliance_rate'] >= 90:
                st.success(f"🎉 Excellent compliance rate: {metrics['compliance_rate']:.1f}%")
            elif metrics['compliance_rate'] >= 75:
                st.info(f"✅ Good compliance rate: {metrics['compliance_rate']:.1f}%")
            elif metrics['compliance_rate'] >= 50:
                st.warning(f"⚠️ Moderate compliance rate: {metrics['compliance_rate']:.1f}%")
            else:
                st.error(f"🚨 Low compliance rate: {metrics['compliance_rate']:.1f}%")
            
            # Enhanced comparison table display
            st.markdown("### 📋 Detailed Compliance Table")
            
            # Apply conditional formatting to compliance column
            def highlight_compliance(val):
                if val == 'Y':
                    return 'background-color: #d4edda; color: #155724;'  # Green
                elif val == 'N':
                    return 'background-color: #f8d7da; color: #721c24;'  # Red
                else:
                    return 'background-color: #fff3cd; color: #856404;'  # Yellow
            
            # Style the dataframe
            styled_df = st.session_state.comparisons_df.copy()
            if 'Compliance (Y/N)' in styled_df.columns:
                st.dataframe(
                    styled_df.style.applymap(
                        highlight_compliance, 
                        subset=['Compliance (Y/N)']
                    ),
                    use_container_width=True, 
                    hide_index=True,
                    height=400
                )
            else:
                st.dataframe(
                    styled_df, 
                    use_container_width=True, 
                    hide_index=True,
                    height=400
                )
            
            # Enhanced download options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = st.session_state.comparisons_df.to_csv(index=False)
                st.download_button(
                    "📥 Download Compliance Table (CSV)",
                    csv_data,
                    f"compliance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Filter for non-compliant items
                if 'Compliance (Y/N)' in styled_df.columns:
                    non_compliant_df = styled_df[styled_df['Compliance (Y/N)'] == 'N']
                    if not non_compliant_df.empty:
                        non_compliant_csv = non_compliant_df.to_csv(index=False)
                        st.download_button(
                            "⚠️ Download Non-Compliant Items",
                            non_compliant_csv,
                            f"non_compliant_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv",
                            use_container_width=True
                        )
                    else:
                        st.success("✅ No non-compliant items!")
            
            with col3:
                # Show summary stats
                with st.popover("📊 View Statistics"):
                    st.write("**Compliance Breakdown:**")
                    st.write(f"- Total items: {metrics['total_parameters']}")
                    st.write(f"- Compliant: {metrics['compliant']} ({metrics['compliance_rate']:.1f}%)")
                    st.write(f"- Non-compliant: {metrics['non_compliant']} ({metrics['non_compliance_rate']:.1f}%)")
                    st.write(f"- Not found: {metrics['not_found']} ({metrics['not_found_rate']:.1f}%)")
            
            # Analysis insights
            if metrics['non_compliant'] > 0 or metrics['not_found'] > 0:
                with st.expander("🔍 Analysis Insights & Recommendations", expanded=False):
                    if metrics['non_compliant'] > 0:
                        st.warning(f"**{metrics['non_compliant']} non-compliant items identified:**")
                        st.markdown("- Review design specifications against building requirements")
                        st.markdown("- Consider design modifications to meet compliance standards")
                        st.markdown("- Consult with relevant authorities for clarification if needed")
                    
                    if metrics['not_found'] > 0:
                        st.info(f"**{metrics['not_found']} items could not be identified in drawings:**")
                        st.markdown("- Verify if missing information exists in other drawing sheets")
                        st.markdown("- Consider requesting additional drawing details from design team")
                        st.markdown("- May require site verification or additional documentation")
            
            # Step 3: Executive Report
            st.markdown("---")
            st.subheader("Step 3: Generate Executive Report & Insights")
            st.markdown("*Generate comprehensive executive report and business insights based on compliance analysis*")
            
            if st.button("📊 Generate Executive Report & Insights", key="generate_report", use_container_width=True):
                with st.spinner("Step 3: Generating executive report and insights..."):
                    # Initialize Agent 3 with custom prompts
                    prompts = get_agent_prompts()
                    agent3 = CombinedExecutiveReporter(model=model)
                    
                    # Set custom prompts if agent supports it
                    if hasattr(agent3, 'set_prompts'):
                        agent3.set_prompts(prompts.get('agent3_combined_reporter', {}))
                    
                    # Process compliance report using agent method
                    processing_result = agent3.process_compliance_report("output/comparison.csv", api_key)
                    
                    if processing_result['report_success'] and processing_result['insights_success']:
                        st.session_state.executive_report = processing_result['report_content']
                        st.session_state.insights_content = processing_result['insights_content']
                        st.session_state.report_summary = processing_result['report_summary']
                        st.session_state.step3_completed = True
                        st.success("✅ Executive report and insights generated successfully")
                    elif processing_result['report_success']:
                        st.session_state.executive_report = processing_result['report_content']
                        st.session_state.report_summary = processing_result['report_summary']
                        st.session_state.step3_completed = True
                        st.warning("⚠️ Executive report generated but insights failed: " + 
                                   processing_result.get('error', 'Unknown error'))
                    else:
                        st.error(f"❌ Report generation failed: {processing_result.get('error')}")
        
        # Display executive report if Step 3 completed
        if st.session_state.step3_completed and st.session_state.executive_report:
            st.subheader("📋 Executive Compliance Report")
            st.markdown(st.session_state.executive_report)
            
            # Summary statistics if available
            if hasattr(st.session_state, 'report_summary'):
                with st.expander("📈 Summary Statistics", expanded=False):
                    st.json(st.session_state.report_summary)
            
            # Display insights if available
            if hasattr(st.session_state, 'insights_content'):
                st.subheader("💡 Detailed Compliance Insights")
                
                # Check if executive_insights.csv exists and display it, fallback to insights.csv
                executive_insights_path = "output/executive_insights.csv"
                insights_path = "output/insights.csv"
                
                if os.path.exists(executive_insights_path):
                    st.subheader("Structured Compliance Analysis")
                    insights_df = pd.read_csv(executive_insights_path)
                    st.dataframe(insights_df, use_container_width=True)
                elif os.path.exists(insights_path):
                    st.subheader("Compliance Metrics")
                    insights_df = pd.read_csv(insights_path)
                    st.dataframe(insights_df, use_container_width=True)
                else:
                    st.warning("Insights CSV file not found.")
                
                # Display raw insights content in expander
                with st.expander("Raw Insights Data", expanded=False):
                    st.code(st.session_state.insights_content)
        
        # Footer
        st.markdown("---")
        st.markdown(
            "*🤖 Powered by AI Agents for automated compliance analysis. "
            "Configure your AI provider in the sidebar for full functionality.*"
        )

if __name__ == "__main__":
    main()


