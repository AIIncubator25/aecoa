"""
🎯 AECOA Orchestrator - Central Coordination System

This is the main orchestration engine that coordinates all AI agents and components.
Handles the complete workflow from YAML processing to executive reporting.

Architecture:
- Manages agent lifecycle and communication
- Coordinates data flow between processing steps  
- Provides unified interface for all AI operations
- Handles error recovery and fallback strategies
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Callable
import pandas as pd
import json
import os
from datetime import datetime
import streamlit as st

# Core system imports
from .core.api_key_manager import api_key_manager

# Agent imports organized by function
from .extractors.agent1_yaml_extractor import YAMLParameterExtractor
from .analyzers.agent2_drawing_analyzer import DrawingAnalysisAgent
from .reporters.agent3_executive_reporter import ExecutiveReportGenerator
from .reporters.agent4_insights_report import InsightsReportGenerator

# Supporting components  
from .providers import ProviderManager
from .model_manager import ModelManager


class AgenticWorkflowOrchestrator:
    def __init__(self):
        self.agents = {}
        self.provider = None
        self.model = None
        self.workflow_state = {
            "current_step": 0,
            "steps_completed": [],
            "checkpoint_results": {},
            "auto_approval": False,
            "execution_log": []
        }
        self.results = {}
    
    def initialize_agents(self, provider: str, model: str, api_key: str = None, 
                         prompts: Dict = None):
        """Initialize all agents with the selected provider and model"""
        try:
            self.provider = provider
            self.model = model
            self.api_key = api_key
            
            # Get API key from centralized manager if not provided
            if not api_key:
                username = st.session_state.get('username')
                api_key = api_key_manager.get_api_key(provider, username)
            
            self.agents = {
                "agent1": YAMLParameterExtractor(model),
                "agent2": DrawingAnalysisAgent(provider, model),
                "agent3": ExecutiveReportGenerator(provider, model),
                "agent4": InsightsReportGenerator(provider, model)
            }
            
            # Set agent prompts if provided
            if prompts:
                self.set_agent_prompts(prompts)
            
            self.log_execution("agents_initialized", {
                "provider": provider,
                "model": model,
                "timestamp": datetime.now().isoformat()
            })
            
            return True, "All agents initialized successfully"
        except Exception as e:
            return False, f"Failed to initialize agents: {str(e)}"
    
    def execute_workflow(self, 
                        yaml_content: str = None,
                        yaml_file_path: str = None,
                        image_files: List[str] = None,
                        selected_api_key: str = None,
                        auto_approval: bool = False,
                        progress_callback: Optional[Callable] = None) -> Tuple[bool, Dict[str, Any]]:
        """Execute the complete 4-agent workflow"""
        
        # Check if agents are initialized before starting workflow
        if not self.agents or len(self.agents) != 4:
            return False, {"error": "Agents not properly initialized. Please click 'Initialize Agents' first."}
        
        self.workflow_state["auto_approval"] = auto_approval
        workflow_results = {"steps": {}, "files_generated": [], "overall_success": False}
        
        try:
            # Step 1: Parameter Definition Agent
            if progress_callback:
                progress_callback(1, "🔍 Agent 1: Extracting parameters from YAML...")
            
            step1_success, step1_result = self._execute_step1(yaml_content, yaml_file_path, selected_api_key)
            workflow_results["steps"]["step1"] = {"success": step1_success, "result": step1_result}
            
            if not step1_success:
                self.log_execution("workflow_failed_step1", step1_result)
                return False, workflow_results
            
            # Checkpoint 1: Review parameter extraction
            if not auto_approval:
                checkpoint1_approved = self._checkpoint_approval(
                    step=1, 
                    title="Parameter Definition Review",
                    description="Review extracted parameters from YAML requirements",
                    data=step1_result
                )
                if not checkpoint1_approved:
                    workflow_results["checkpoint_cancelled"] = 1
                    return False, workflow_results
            
            # Step 2: Drawing Analysis Agent
            if progress_callback:
                progress_callback(2, "📐 Agent 2: Analyzing drawings for measurements...")
            
            step2_success, step2_result = self._execute_step2(image_files, "parameters.csv", selected_api_key)
            workflow_results["steps"]["step2"] = {"success": step2_success, "result": step2_result}
            
            if not step2_success:
                self.log_execution("workflow_failed_step2", step2_result)
                return False, workflow_results
            
            # Checkpoint 2: Review drawing analysis
            if not auto_approval:
                checkpoint2_approved = self._checkpoint_approval(
                    step=2,
                    title="Drawing Analysis Review", 
                    description="Review measurements extracted from drawings",
                    data=step2_result
                )
                if not checkpoint2_approved:
                    workflow_results["checkpoint_cancelled"] = 2
                    return False, workflow_results
            
            # Step 3: Compliance Comparison Agent
            if progress_callback:
                progress_callback(3, "⚖️ Agent 3: Comparing findings with requirements...")
            
            step3_success, step3_result = self._execute_step3("parameters.csv", "drawings_analysis.csv", selected_api_key)
            workflow_results["steps"]["step3"] = {"success": step3_success, "result": step3_result}
            
            if not step3_success:
                self.log_execution("workflow_failed_step3", step3_result)
                return False, workflow_results
            
            # Checkpoint 3: Review compliance results
            if not auto_approval:
                checkpoint3_approved = self._checkpoint_approval(
                    step=3,
                    title="Compliance Analysis Review",
                    description="Review compliance determination results", 
                    data=step3_result
                )
                if not checkpoint3_approved:
                    workflow_results["checkpoint_cancelled"] = 3
                    return False, workflow_results
            
            # Step 4: Insights & Report Agent
            if progress_callback:
                progress_callback(4, "📊 Agent 4: Generating insights and recommendations...")
            
            step4_success, step4_result = self._execute_step4("comparisons.csv", selected_api_key)
            workflow_results["steps"]["step4"] = {"success": step4_success, "result": step4_result}
            
            if not step4_success:
                self.log_execution("workflow_failed_step4", step4_result)
                return False, workflow_results
            
            # Final checkpoint: Review final report
            if not auto_approval:
                checkpoint4_approved = self._checkpoint_approval(
                    step=4,
                    title="Final Report Review",
                    description="Review executive summary and recommendations",
                    data=step4_result
                )
                if not checkpoint4_approved:
                    workflow_results["checkpoint_cancelled"] = 4
                    return False, workflow_results
            
            # Workflow completed successfully
            workflow_results["overall_success"] = True
            workflow_results["files_generated"] = ["defined_parameters.csv", "drawings_analysis.csv", "comparisons.csv", "report.csv"]
            workflow_results["completion_time"] = datetime.now().isoformat()
            
            self.log_execution("workflow_completed", workflow_results)
            
            if progress_callback:
                progress_callback(5, "✅ Workflow completed successfully!")
            
            return True, workflow_results
            
        except Exception as e:
            error_result = {"error": f"Workflow execution failed: {str(e)}"}
            self.log_execution("workflow_error", error_result)
            workflow_results["error"] = error_result
            return False, workflow_results
    
    def _execute_step1(self, yaml_content: str, yaml_file_path: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Execute Agent 1: Parameter Definition"""
        try:
            # Check if agents are initialized
            if not self.agents or "agent1" not in self.agents:
                return False, {"error": "Agent 1 not initialized. Please click 'Initialize Agents' first."}
            
            agent1 = self.agents["agent1"]
            success, result = agent1.extract_parameters(yaml_content, yaml_file_path, selected_api_key)
            
            # Save results for future reference
            self.results["step1_parameter_definition"] = {
                "success": success,
                "result": result
            }
            
            self.log_execution("step1_completed", {
                "success": success,
                "parameters_count": result.get("parameters_count", 0) if success else 0,
                "csv_generated": "defined_parameters.csv" in str(result)
            })
            
            return success, result
        except Exception as e:
            return False, {"error": f"Step 1 failed: {str(e)}"}
    
    def _execute_step2(self, image_files: List[str], parameters_csv: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Execute Agent 2: Drawing Analysis"""
        try:
            # Check if agents are initialized
            if not self.agents or "agent2" not in self.agents:
                return False, {"error": "Agent 2 not initialized. Please click 'Initialize Agents' first."}
            
            agent2 = self.agents["agent2"]
            success, result = agent2.analyze_drawings(image_files, parameters_csv, selected_api_key)
            
            # Save results for future reference
            self.results["step2_drawing_analysis"] = {
                "success": success,
                "result": result
            }
            
            self.log_execution("step2_completed", {
                "success": success,
                "images_processed": len(image_files) if image_files else 0,
                "measurements_found": result.get("measurements_count", 0) if success else 0,
                "csv_generated": "drawings_analysis.csv" in str(result)
            })
            
            return success, result
        except Exception as e:
            return False, {"error": f"Step 2 failed: {str(e)}"}
    
    def _execute_step3(self, parameters_csv: str, analysis_csv: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Execute Agent 3: Compliance Comparison"""
        try:
            # Check if agents are initialized
            if not self.agents or "agent3" not in self.agents:
                return False, {"error": "Agent 3 not initialized. Please click 'Initialize Agents' first."}
            
            agent3 = self.agents["agent3"]
            success, result = agent3.compare_compliance(parameters_csv, analysis_csv, selected_api_key)
            
            self.log_execution("step3_completed", {
                "success": success,
                "compliance_results": result.get("total_parameters", 0) if success else 0,
                "csv_generated": "comparisons.csv" in str(result)
            })
            
            return success, result
        except Exception as e:
            return False, {"error": f"Step 3 failed: {str(e)}"}
    
    def _execute_step4(self, comparisons_csv: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Execute Agent 4: Insights & Report"""
        try:
            # Check if agents are initialized
            if not self.agents or "agent4" not in self.agents:
                return False, {"error": "Agent 4 not initialized. Please click 'Initialize Agents' first."}
            
            agent4 = self.agents["agent4"]  
            success, result = agent4.generate_insights_report(comparisons_csv, selected_api_key)
            
            self.log_execution("step4_completed", {
                "success": success,
                "insights_generated": "executive_summary" in str(result) if success else False,
                "csv_generated": "report.csv" in str(result)
            })
            
            return success, result
        except Exception as e:
            return False, {"error": f"Step 4 failed: {str(e)}"}
    
    def _checkpoint_approval(self, step: int, title: str, description: str, data: Dict[str, Any]) -> bool:
        """Handle human-in-the-loop checkpoint approval with Streamlit UI"""
        
        checkpoint_info = {
            "step": step,
            "title": title,
            "description": description,
            "data_preview": str(data)[:500],  # Longer preview
            "timestamp": datetime.now().isoformat()
        }
        
        self.workflow_state["checkpoint_results"][f"step_{step}"] = checkpoint_info
        
        # If auto-approval is enabled, always approve
        if self.workflow_state.get("auto_approval", False):
            self.log_execution(f"checkpoint_{step}_auto_approved", checkpoint_info)
            # Auto-save parameters for step 1 if available
            if step == 1 and 'extracted_df' in data:
                data['extracted_df'].to_csv("parameters.csv", index=False)
            return True
        
        # Manual approval mode - display results and ask for confirmation
        return self._interactive_checkpoint_ui(step, title, description, data)
    
    def _interactive_checkpoint_ui(self, step: int, title: str, description: str, data: Dict[str, Any]) -> bool:
        """Display interactive checkpoint UI and get user approval"""
        import streamlit as st
        
        # Create a distinctive checkpoint section
        st.markdown("---")
        st.markdown(f"## 🛑 **Checkpoint {step}: {title}**")
        st.markdown(f"**{description}**")
        
        # Display results preview with editing capability
        if step == 1:  # Parameter extraction results - ALLOW EDITING
            return self._handle_step1_checkpoint(data)
        else:
            # For other steps, just show a simple approval
            return self._handle_general_checkpoint(step, title, data)
    
    def _handle_step1_checkpoint(self, data: Dict[str, Any]) -> bool:
        """Handle Step 1 checkpoint with parameter editing and a single proceed button."""
        import streamlit as st
        
        st.markdown("### 📋 **Extracted Parameters - Review & Edit**")
        
        if "parameters_df" in data:
            df = data["parameters_df"].copy()
            
            # Convert all object columns to strings to avoid PyArrow conversion issues
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str)
                    
            st.info(f"**Found {len(df)} parameters from your YAML requirements.** You can edit them below.")
            
            # Use st.data_editor for interactive editing
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                key="parameter_editor",
                hide_index=True
            )
            
            # Check if parameters have been saved already
            params_saved_key = f"checkpoint_1_params_saved"
            params_saved = st.session_state.get(params_saved_key, False)
            
            if not params_saved:
                # Show primary button for first save
                save_button = st.button(
                    "✅ Save Parameters & Proceed to Drawing Analysis", 
                    type="primary", 
                    use_container_width=True
                )
                if save_button:
                    try:
                        # Save the CSV file
                        csv_path = "parameters.csv"
                        edited_df.to_csv(csv_path, index=False)
                        
                        # Update session state
                        st.session_state["checkpoint_1_decision"] = "approved"
                        st.session_state["edited_parameters_df"] = edited_df
                        st.session_state[params_saved_key] = True
                        
                        self.log_execution("checkpoint_1_approved", {
                            "step": 1,
                            "final_count": len(edited_df),
                            "user_modified": not edited_df.equals(df)
                        })
                        
                        # Force rerun to show the new state
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Failed to save parameters: {e}")
                        return False
            else:
                # Show black filled button indicating completion
                completion_button = st.button(
                    "✅ Parameters Saved Successfully", 
                    type="secondary", 
                    use_container_width=True, 
                    disabled=True
                )
                
                # Show file location and next steps
                import os
                csv_path = os.path.abspath("parameters.csv")
                st.success(f"📁 **Parameters saved to:** `{csv_path}`")
                
                st.info("""
                **📐 Next Step: Provide Technical Drawings**
                
                Please upload your technical drawings (DXF, PDF, or image files) for analysis against these parameters:
                - Navigate to the main interface or drawing upload section
                - Upload your architectural/engineering drawings
                - The system will analyze measurements and compliance against the saved parameters
                """)
                
                # Add a note about what parameters were saved
                param_count = len(edited_df)
                st.markdown(
                    f"**📊 Ready for analysis:** {param_count} parameters "
                    "extracted and saved"
                )
                
                # Option to re-edit if needed
                if st.button("📝 Re-edit Parameters", type="secondary", use_container_width=True):
                    st.session_state[params_saved_key] = False
                    st.rerun()
                
                return True
        else:
            st.error("No parameters found to review.")
            return False
            
        return False
        
    def _handle_general_checkpoint(self, step: int, title: str, data: Dict[str, Any]) -> bool:
        """Handle checkpoints for steps 2, 3, 4 (non-editable)"""
        import streamlit as st
        
        # Display results preview
        with st.expander(f"📊 Review Step {step} Results", expanded=True):
            
            if step == 2:  # Drawing analysis results  
                if "measurements_df" in data:
                    st.markdown("**📐 Measurements from Drawings:**")
                    # Convert any object columns to strings to prevent PyArrow errors
                    df = data["measurements_df"].copy()
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].astype(str)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.markdown(f"**✅ Analyzed {data.get('measurements_count', 0)} measurements**")
                    if "csv_saved" in data:
                        st.success(f"✅ Saved as: {data['csv_saved']}")
                
            elif step == 3:  # Compliance comparison results
                if "comparisons_df" in data:
                    st.markdown("**⚖️ Compliance Analysis:**")
                    # Convert any object columns to strings to prevent PyArrow errors
                    df = data["comparisons_df"].copy()
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].astype(str)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Show compliance summary if available
                    if "compliance_summary" in data:
                        summary = data["compliance_summary"]
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("✅ Meets", summary.get("meets", 0))
                        with col2:
                            st.metric("❌ Below Min", summary.get("below_min", 0))
                        with col3:
                            st.metric("⚠️ Check", summary.get("check", 0))
                        with col4:
                            st.metric("➖ N/A", summary.get("not_applicable", 0))
                    
                    if "csv_saved" in data:
                        st.success(f"✅ Saved as: {data['csv_saved']}")
                
            elif step == 4:  # Final insights and report
                if "executive_summary" in data:
                    summary = data["executive_summary"]
                    st.markdown("**📊 Executive Summary:**")
                    st.markdown(f"**Overall Status:** {summary.get('overall_compliance_status', 'Unknown')}")
                    st.markdown(f"**Compliance Score:** {summary.get('compliance_score', 'Not calculated')}")
                    
                    if summary.get("key_findings"):
                        st.markdown("**🔍 Key Findings:**")
                        for finding in summary["key_findings"]:
                            st.markdown(f"• {finding}")
                
                if "report_df" in data:
                    st.markdown("**📄 Final Report Preview:**")
                    # Convert any object columns to strings to prevent PyArrow errors
                    df = data["report_df"].copy()
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            df[col] = df[col].astype(str)
                    st.dataframe(df.head(10), use_container_width=True, hide_index=True)
                    
                if "csv_saved" in data:
                    st.success(f"✅ Saved as: {data['csv_saved']}")
        
        # Approval buttons
        st.markdown("### 🤔 Approve this step to continue?")
        col1, col2, col3 = st.columns([1, 1, 2])
        
        checkpoint_key = f"checkpoint_{step}_decision"
        
        with col1:
            if st.button(f"✅ Approve Step {step}", key=f"approve_{step}", type="primary"):
                st.session_state[checkpoint_key] = "approved"
                self.log_execution(f"checkpoint_{step}_approved", {"step": step, "title": title})
                st.success(f"✅ Step {step} approved! Continuing to next step...")
                return True
        
        with col2:
            if st.button(f"❌ Reject Step {step}", key=f"reject_{step}"):
                st.session_state[checkpoint_key] = "rejected"
                self.log_execution(f"checkpoint_{step}_rejected", {"step": step, "title": title})
                st.error(f"❌ Step {step} rejected. Workflow stopped.")
                return False
        
        with col3:
            st.markdown("*Review the results above and decide whether to continue.*")
        
        # Check if user has already made a decision
        if checkpoint_key in st.session_state:
            decision = st.session_state[checkpoint_key]
            if decision == "approved":
                st.success(f"✅ Step {step} previously approved")
                return True
            elif decision == "rejected":
                st.error(f"❌ Step {step} was rejected")
                return False
        
        # Default: waiting for user decision
        st.info("⏳ Waiting for your approval to continue...")
        return False
    
    def log_execution(self, event: str, data: Dict[str, Any]):
        """Log workflow execution events"""
        log_entry = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.workflow_state["execution_log"].append(log_entry)
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "current_step": self.workflow_state["current_step"],
            "steps_completed": self.workflow_state["steps_completed"],
            "auto_approval": self.workflow_state["auto_approval"],
            "execution_log": self.workflow_state["execution_log"][-5:],  # Last 5 entries
            "agents_initialized": len(self.agents) == 4
        }
    
    def get_all_logs(self):
        """Get all execution logs and agent logs."""
        logs = {
            "workflow": self.workflow_state["execution_log"],
            "agents": {}
        }
        
        # Collect logs from each agent
        for agent_name, agent in self.agents.items():
            if hasattr(agent, 'get_prompt_log') and hasattr(agent, 'get_response_log'):
                logs["agents"][agent_name] = {
                    "prompts": agent.get_prompt_log(),
                    "responses": agent.get_response_log()
                }
        
        return logs
        
    def requires_checkpoint(self, step_number: int) -> bool:
        """Check if a specific step requires user checkpoint approval."""
        current_step = self.workflow_state.get("current_step", 0)
        steps_completed = self.workflow_state.get("steps_completed", [])
        # Map step numbers to stored result keys
        key_map = {
            1: "step1_parameter_definition",
            2: "step2_drawing_analysis",
            3: "step3_compliance_comparison",
            4: "step4_insights_and_reporting",
        }
        key = key_map.get(step_number)
        if key is None:
            return False
        # Requires checkpoint if we have data for the step and it's not marked completed yet
        if step_number <= current_step and step_number not in steps_completed:
            return key in self.results
        return False
        
    def is_step_completed(self, step_number: int) -> bool:
        """Check if a specific step has been completed."""
        return step_number in self.workflow_state.get("steps_completed", [])
        
    def get_current_step_name(self) -> str:
        """Get the name of the current step."""
        step_map = {
            0: "Initializing",
            1: "Parameter Definition",
            2: "Drawing Analysis",
            3: "Compliance Comparison",
            4: "Insights and Reporting"
        }
        return step_map.get(self.workflow_state.get("current_step", 0), "Unknown Step")
        
    def set_files(self, yaml_file, drawing_files):
        """Set the input files for the workflow.
        
        Args:
            yaml_file: The uploaded YAML file from Streamlit (st.file_uploader)
            drawing_files: The uploaded drawing files from Streamlit (st.file_uploader)
        """
        import os
        import tempfile
        
        self.yaml_file = yaml_file
        self.drawing_files = drawing_files
        
        # Save the uploaded YAML content
        if yaml_file:
            yaml_content = yaml_file.read().decode("utf-8")
            self.yaml_content = yaml_content
            # Reset the file pointer for future use
            yaml_file.seek(0)
            
        # Save drawing files to temporary locations
        self.drawing_file_paths = []
        if drawing_files:
            for drawing_file in drawing_files:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(drawing_file.name)[1]) as temp_file:
                    temp_file.write(drawing_file.read())
                    self.drawing_file_paths.append(temp_file.name)
                # Reset the file pointer for future use
                drawing_file.seek(0)
        
    def reset_results(self):
        """Reset the results of the workflow."""
        self.results = {}
        
    def is_workflow_finished(self):
        """Check if the workflow is finished."""
        # Workflow is finished when all steps are completed
        return len(self.workflow_state.get("steps_completed", [])) >= 4
        
    def get_result(self, key):
        """Get a specific result from the workflow."""
        data = self.results.get(key)
        if data is None:
            return None
        # Flatten nested { success, result: {...} } structure for UI compatibility
        if isinstance(data, dict) and isinstance(data.get("result"), dict):
            combined = dict(data["result"])  # copy inner result
            # Preserve top-level success
            if "success" in data and "success" not in combined:
                combined["success"] = data["success"]
            # Backward-compatibility mappings for UI
            if key == "step3_compliance_comparison":
                # app.py expects 'comparison_df'
                if "comparison_df" not in combined and "compliance_df" in combined:
                    combined["comparison_df"] = combined["compliance_df"]
            if key == "step4_insights_and_reporting":
                # Provide a simple markdown report if not present
                if "report" not in combined:
                    summary = combined.get("executive_summary", {})
                    dashboard = combined.get("executive_dashboard", {})
                    lines = []
                    if dashboard:
                        lines.append(f"## Executive Dashboard\n- Overall Status: {dashboard.get('overall_status', 'Unknown')}\n- Compliance Grade: {dashboard.get('compliance_grade', 'N/A')}\n- Business Impact Score: {dashboard.get('business_impact_score', 'N/A')}")
                    if summary:
                        lines.append("## Executive Summary")
                        if isinstance(summary, dict):
                            for k, v in summary.items():
                                # Render lists and scalars succinctly
                                if isinstance(v, list):
                                    if v:
                                        lines.append(f"- {k.replace('_',' ').title()}:")
                                        lines.extend([f"  - {item}" for item in v])
                                else:
                                    lines.append(f"- {k.replace('_',' ').title()}: {v}")
                        else:
                            lines.append(str(summary))
                    if lines:
                        combined["report"] = "\n".join(lines)
            return combined
        return data
        
    def run_current_step(self):
        """Run the current step of the workflow."""
        import streamlit as st
        
        current_step = self.workflow_state.get("current_step", 0)
        
        if current_step == 0:
            # Initialize step
            self.workflow_state["current_step"] = 1
            return True
            
        elif current_step == 1:
            # Run Agent 1: Parameter Definition
            with st.spinner("🔍 Agent 1: Extracting parameters from YAML..."):
                if hasattr(self, 'yaml_content'):
                    success, result = self._execute_step1(self.yaml_content, None, self.api_key)
                else:
                    success, result = self._execute_step1(None, "yaml_file.yaml", self.api_key)
                
                if success:
                    self.workflow_state["current_step"] = 2
                return success
                
        elif current_step == 2:
            # Run Agent 2: Drawing Analysis
            with st.spinner("📐 Agent 2: Analyzing drawings for measurements..."):
                if hasattr(self, 'drawing_file_paths') and self.drawing_file_paths:
                    success, result = self._execute_step2(self.drawing_file_paths, "parameters.csv", self.api_key)
                else:
                    success = False
                    result = {"error": "No drawing files available."}
                
                if success:
                    self.workflow_state["current_step"] = 3
                return success
                
        elif current_step == 3:
            # Run Agent 3: Compliance Comparison
            with st.spinner("⚖️ Agent 3: Comparing with requirements..."):
                success, result = self._execute_step3("parameters.csv", "drawings_analysis.csv", self.api_key)
                
                if success:
                    self.workflow_state["current_step"] = 4
                    # Mark step 3 as completed so UI can display results
                    if 3 not in self.workflow_state["steps_completed"]:
                        self.workflow_state["steps_completed"].append(3)
                return success
                
        elif current_step == 4:
            # Run Agent 4: Insights Report
            with st.spinner("📊 Agent 4: Generating insights and report..."):
                success, result = self._execute_step4("comparisons.csv", self.api_key)
                
                if success:
                    if 4 not in self.workflow_state["steps_completed"]:
                        self.workflow_state["steps_completed"].append(4)
                return success
        
        return False
        
    def handle_step1_checkpoint(self):
        """Handle the checkpoint for step 1."""
        import streamlit as st
        
        # Get the result data for step 1
        step1_result = self.results.get("step1_parameter_definition")
        
        if step1_result and step1_result.get("success"):
            data = step1_result.get("result", {})
            return self._handle_step1_checkpoint(data)
        elif step1_result:
            st.error(f"Parameter extraction failed: {step1_result.get('error')}")
            return False
        else:
            st.info("No parameter data available yet.")
            return False
        
    def handle_step2_checkpoint(self):
        """Handle the checkpoint for step 2."""
        import streamlit as st
        
        # Get the result data for step 2
        step2_result = self.results.get("step2_drawing_analysis")
        
        if step2_result and step2_result.get("success"):
            data = step2_result.get("result", {})
            
            with st.expander("Review Step 2 Results", expanded=True):
                st.markdown("### 📐 Drawing Analysis Results")
                
                if "analysis_df" in data:
                    st.dataframe(data["analysis_df"], use_container_width=True, hide_index=True)
                    st.success(f"✅ Analysis saved to: {data.get('csv_saved', 'drawings_analysis.csv')}")
                    
                    # Display titles and tables if available
                    if "titles_and_tables" in data:
                        titles_tables = data["titles_and_tables"]
                        
                        if "drawing_titles" in titles_tables:
                            st.subheader("📑 Drawing Titles")
                            for idx, title in enumerate(titles_tables["drawing_titles"]):
                                st.markdown(f"**{idx+1}.** {title}")
                        
                        if "extracted_tables" in titles_tables and titles_tables["extracted_tables"]:
                            st.subheader("📊 Extracted Tables")
                            for idx, table in enumerate(titles_tables["extracted_tables"]):
                                st.markdown(f"**Table {idx+1}** from: {table.get('drawing_title', 'Unknown')}")
                                
                                # Convert table data to DataFrame for display
                                if "table_data" in table and table["table_data"]:
                                    try:
                                        headers = table["table_data"][0]
                                        rows = table["table_data"][1:]
                                        df = pd.DataFrame(rows, columns=headers)
                                        st.dataframe(df, use_container_width=True, hide_index=True)
                                    except:
                                        # Fallback if conversion fails
                                        st.table(table["table_data"])
                else:
                    st.warning("No analysis data available.")
                
            # Approve/Reject buttons
            st.write("Review the results above and decide whether to continue.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Approve Step 2", type="primary", key="approve_step2"):
                    self.workflow_state["steps_completed"].append(2)
                    st.success("Drawing analysis approved. Proceeding to next step...")
                    return True
                
            with col2:
                if st.button("❌ Reject Step 2", key="reject_step2"):
                    st.error("Drawing analysis rejected.")
                    return False
        
        elif step2_result:
            st.error(f"Drawing analysis failed: {step2_result.get('error')}")
            return False
        else:
            st.info("No drawing analysis data available yet.")
            return False
        
    def get_all_logs(self):
        """Get all logs from the workflow."""
        agent_logs = {}
        
        # For each agent, try to get both prompt and response logs
        for agent_key, agent in self.agents.items():
            try:
                # Get prompt log if the method exists
                prompt_log = agent.get_prompt_log() if hasattr(agent, 'get_prompt_log') else []
                # Get response log if the method exists
                response_log = agent.get_response_log() if hasattr(agent, 'get_response_log') else []
                # Add both to the agent logs
                agent_logs[agent_key] = {
                    "prompt_log": prompt_log,
                    "response_log": response_log
                }
            except Exception as e:
                agent_logs[agent_key] = {"error": f"Could not get logs: {str(e)}"}
        
        return {
            "workflow_state": self.workflow_state,
            "agent_logs": agent_logs
        }
    
    def get_agent_logs(self, agent_name: str) -> Tuple[List[Dict], List[Dict]]:
        """Get prompt and response logs from a specific agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            if hasattr(agent, 'get_prompt_log') and hasattr(agent, 'get_response_log'):
                return agent.get_prompt_log(), agent.get_response_log()
        return [], []
    
    def clear_all_logs(self):
        """Clear all logs from agents and orchestrator"""
        for agent in self.agents.values():
            agent.clear_logs()
        self.workflow_state["execution_log"] = []
    
    def reset_workflow(self):
        """Reset workflow state for new execution"""
        self.workflow_state = {
            "current_step": 0,
            "steps_completed": [],
            "checkpoint_results": {},
            "auto_approval": False,
            "execution_log": []
        }
        self.results = {}
        
        # Clear agent logs
        self.clear_all_logs()
        
    def set_agent_prompts(self, prompts_dict: Dict[str, Dict[str, str]]):
        """Set custom prompts for all agents from app.py"""
        if not self.agents:
            return False, "Agents not initialized. Please initialize agents first."
            
        try:
            # Set Agent 1 prompts
            if "Agent1" in prompts_dict and self.agents.get("agent1"):
                self.agents["agent1"].set_custom_prompts(
                    combined_prompt=prompts_dict["Agent1"].get("user")
                )
                
            # Set Agent 2 prompts
            if "Agent2" in prompts_dict and self.agents.get("agent2"):
                self.agents["agent2"].set_custom_prompts(
                    system_prompt=prompts_dict["Agent2"].get("system"),
                    user_prompt=prompts_dict["Agent2"].get("user")
                )
                
            # Set Agent 3 prompts (if it has a set_custom_prompts method)
            if "Agent3" in prompts_dict and self.agents.get("agent3") and hasattr(self.agents["agent3"], "set_custom_prompts"):
                self.agents["agent3"].set_custom_prompts(
                    system_prompt=prompts_dict["Agent3"].get("system"),
                    user_prompt=prompts_dict["Agent3"].get("user")
                )
                
            # Set Agent 4 prompts (if it has a set_custom_prompts method)
            if "Agent4" in prompts_dict and self.agents.get("agent4") and hasattr(self.agents["agent4"], "set_custom_prompts"):
                self.agents["agent4"].set_custom_prompts(
                    system_prompt=prompts_dict["Agent4"].get("system"),
                    user_prompt=prompts_dict["Agent4"].get("user")
                )
                
            return True, "Agent prompts set successfully"
        except Exception as e:
            return False, f"Error setting agent prompts: {str(e)}"


# Legacy API compatibility (kept for backward compatibility)
def analyze_image_from_bytes(image_bytes: bytes, yaml_text: Optional[str], provider_hint: Optional[str]=None, model_hint: Optional[str]=None) -> Dict[str, Any]:
    """Legacy function - kept for backward compatibility"""
    try:
        from .providers import call_provider
        from .postprocess import build_result_bundle
        provider, model = call_provider.auto_select(provider_hint, model_hint)
        result = call_provider.extract_from_image(image_bytes=image_bytes, provider=provider, model=model)
        return build_result_bundle(yaml_text, result)
    except ImportError:
        return {"error": "Legacy providers not available"}

def analyze_dxf_from_bytes(dxf_bytes: bytes, yaml_text: Optional[str], provider_hint: Optional[str]=None, model_hint: Optional[str]=None) -> Dict[str, Any]:
    """Legacy function - kept for backward compatibility"""
    try:
        from .providers import call_provider
        from .postprocess import build_result_bundle
        provider, model = call_provider.auto_select(provider_hint, model_hint)
        result = call_provider.extract_from_dxf(dxf_bytes=dxf_bytes, provider=provider, model=model)
        return build_result_bundle(yaml_text, result)
    except ImportError:
        return {"error": "Legacy providers not available"}
