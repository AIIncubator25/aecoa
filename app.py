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
from typing import Optional

# Import authentication system
from agents.auth.auth import StreamlitAuth

# Import core functionality
from agents.core.api_key_manager import api_key_manager

# Import our organized agents
from agents.parsers.agent1_unified_processor import UnifiedDocumentProcessor
from agents.analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent
from agents.reporters.agent3_executive_reporter import ExecutiveReportGenerator
from agents.reporters.agent4_insights_report import InsightsReportAgent

# Import orchestrator for complex workflows
from agents.orchestrator import AgenticWorkflowOrchestrator

# --- Centralized Prompt Management ---
DEFAULT_PROMPTS = {
    "agent1_unified_processor": UnifiedDocumentProcessor.get_default_prompts(),
    "agent2_drawing_analyzer": DrawingAnalysisAgent.get_default_prompts(),
    "agent3_executive_reporter": ExecutiveReportGenerator.get_default_prompts(),
    "agent4_insights_report": InsightsReportAgent.get_default_prompts()
}

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
            "agent3_executive_reporter": "Step 3 - Executive Report Generator",
            "agent4_insights_report": "Step 4 - Insights Generator"
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
        page_title="AEC Compliance Analysis",
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
                        default_model = "llama3.2:latest"
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
            st.markdown(f"**Step 3**: Executive Report Generator")
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
        
        drawing_files = st.file_uploader(
            "Choose drawing files",
            type=['jpg', 'jpeg', 'png', 'dxf'],
            accept_multiple_files=True,
            key="drawing_uploader"
        )
        
        if drawing_files:
            # Initialize Agent 2 for file processing
            agent2 = DrawingAnalysisAgent(model=model)
            file_summary = agent2.get_file_summary(drawing_files)
            
            # Show file summary
            st.info(f"📁 Uploaded: {file_summary['image_files']} image files, {file_summary['dxf_files']} DXF files")
            if file_summary['dxf_files'] > 0:
                st.warning("⚠️ DXF files are saved but not yet processed by AI analysis")
            
            if st.button("🔍 Analyze Drawings", key="analyze_drawings", use_container_width=True):
                with st.spinner("Step 2: Analyzing drawings for compliance..."):
                    # Get custom prompts
                    prompts = get_agent_prompts()
                    
                    # Set custom prompts if agent supports it
                    if hasattr(agent2, 'set_prompts'):
                        agent2.set_prompts(prompts['agent2_drawing_analyzer'])
                    
                    # Process drawings using agent method
                    processing_result = agent2.process_drawing_files(drawing_files, "parameters.csv", api_key)
                    
                    if processing_result['analysis_success']:
                        analysis_result = processing_result['analysis_result']
                        st.session_state.comparisons_df = analysis_result['comparisons_df']
                        st.session_state.step2_completed = True
                        st.success(f"✅ Drawing analysis completed using {analysis_result.get('method', 'Unknown')} method")
                        st.info(analysis_result.get('info', ''))
                        
                        # Show drawing titles if available
                        if 'drawing_titles' in analysis_result and analysis_result['drawing_titles']:
                            st.markdown("**📋 Identified Drawing Titles:**")
                            for title in analysis_result['drawing_titles']:
                                st.markdown(f"- {title}")
                    else:
                        st.error(f"❌ Drawing analysis failed: {processing_result.get('error')}")
    
        # Display compliance comparison if Step 2 completed
        if st.session_state.step2_completed and st.session_state.comparisons_df is not None:
            st.subheader("🔍 Compliance Comparison Results")
            
            # Get compliance metrics using agent method
            agent2 = DrawingAnalysisAgent()
            metrics = agent2.get_compliance_metrics(st.session_state.comparisons_df)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Parameters", metrics['total_parameters'])
            with col2:
                st.metric("Compliant", metrics['compliant'], delta=f"{metrics['compliance_rate']:.1f}%")
            with col3:
                st.metric("Non-Compliant", metrics['non_compliant'], delta=f"-{metrics['non_compliance_rate']:.1f}%")
            with col4:
                st.metric("Not Found", metrics['not_found'], delta=f"{metrics['not_found_rate']:.1f}%")
            
            # Full comparison table
            st.dataframe(st.session_state.comparisons_df, use_container_width=True, hide_index=True)
            
            # Download button
            csv_data = st.session_state.comparisons_df.to_csv(index=False)
            st.download_button(
                "📥 Download comparisons.csv",
                csv_data,
                "comparisons.csv",
                "text/csv",
                use_container_width=True
            )
            
            # Step 3: Executive Report
            st.markdown("---")
            st.subheader("Step 3: Generate Executive Report")
            st.markdown("*Generate comprehensive insights and recommendations based on compliance analysis*")
            
            if st.button("📊 Generate Executive Report", key="generate_report", use_container_width=True):
                with st.spinner("Step 3: Generating executive report and insights..."):
                    # Initialize Agent 3 with custom prompts
                    prompts = get_agent_prompts()
                    agent3 = ExecutiveReportGenerator(model=model)
                    
                    # Set custom prompts if agent supports it
                    if hasattr(agent3, 'set_prompts'):
                        agent3.set_prompts(prompts['agent3_executive_reporter'])
                    
                    # Process compliance report using agent method
                    processing_result = agent3.process_compliance_report("comparisons.csv", api_key)
                    
                    if processing_result['report_success']:
                        st.session_state.executive_report = processing_result['report_content']
                        st.session_state.report_summary = processing_result['report_summary']
                        st.session_state.step3_completed = True
                        st.success("✅ Executive report generated successfully")
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
        
        # Footer
        st.markdown("---")
        st.markdown(
            "*🤖 Powered by AI Agents for automated compliance analysis. "
            "Configure your AI provider in the sidebar for full functionality.*"
        )

if __name__ == "__main__":
    main()


