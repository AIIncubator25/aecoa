"""
Agent 1: YAML Parameter Extractor
Parses YAML files and extracts compliance parameters into a structured 9x7 table.
"""
import os
import yaml
import pandas as pd
import requests
import json
from typing import Tuple, Dict, Any

# Agent 1's Default Prompt - AEC Compliance Component Detector
DEFAULT_PROMPT = """SYSTEM
You are an AEC compliance table extractor. Follow the YAML spec strictly.

Goal:
1) Extract OBSERVED parameters/components that appear in the YAML structure (evidence-first).
2) Map OBSERVED items to canonical names when possible.
3) Produce SUGGESTED (speculative) parameters that are typical for the detected component(s) but not present in the YAML.

Rules:
- NEVER invent observed values. Each OBSERVED item must cite literal evidence from YAML structure (csv_schema rows, parameter_templates, compliance_rules) with exact field reference.
- Normalize units to standard AEC units (mm, m, m², m³, %, nos); if not possible, return "na".
- For values like "1.08 (3*0.36)", keep the first numeric token only (1.08).
- Distinguish clearly: "observed" vs "suggested".
- Return STRICT JSON only—no prose.

USER
Inputs:
1) YAML spec (text): {yaml_content}

Tasks:
- Detect component(s) via YAML structure analysis, csv_schema entries, parameter names, units, and clause references.
- Extract OBSERVED parameters from YAML:
  * original_parameter: raw YAML field/row text  
  * canonical_parameter: normalized AEC parameter name
  * value + unit (normalized), or "na"
  * component, clause (if present), yaml_path
  * provenance: yaml_section, field_name, evidence_text, confidence
- Generate SUGGESTED parameters that are common for detected AEC components but NOT observed in YAML. No values—just names and rationale.

Output JSON schema:
{{
  "doc_meta": {{"yaml_sections": ["string"]}},
  "components_detected": ["string"],
  "observed": [
    {{
      "component": "string",
      "original_parameter": "string", 
      "canonical_parameter": "string",
      "value": "number | string | na",
      "unit": "mm|m|m²|m³|%|nos|text|na",
      "clause": "string | na",
      "yaml_path": "string",
      "provenance": {{"yaml_section": "string", "field_name": "string", "evidence_text": "string", "conf": "number"}}
    }}
  ],
  "suggested": [
    {{
      "component": "string", 
      "parameter": "string",
      "reason": "string",
      "conf": "number"
    }}
  ]
}}

Notes:
- Only place items in "observed" when there is explicit YAML structural evidence.
- Place AEC domain expectations without YAML evidence in "suggested" only.
- Focus on building components: walls, slabs, openings, spaces, clearances, areas, volumes.
- Detect components like: Household Shelter, Floor Slab, Ceiling, Staircase, Ventilation, etc.

RUNTIME SETTINGS (recommended)
- Temperature: 0 (or equivalent) for deterministic output."""

class YAMLParameterExtractor:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.prompt = DEFAULT_PROMPT
        
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent (compatibility with app.py)."""
        return {"user": DEFAULT_PROMPT}
        
    def set_prompts(self, prompts: Dict[str, str]):
        """Set custom prompt for the agent."""
        self.prompt = prompts.get("user", prompts.get("system", DEFAULT_PROMPT))
    
    def parse_yaml_content(self, yaml_content: str) -> Tuple[bool, Dict[str, Any]]:
        """Parse YAML content and extract structure."""
        try:
            import yaml
            yaml_data = yaml.safe_load(yaml_content)
            return True, yaml_data
        except Exception as e:
            return False, {"error": f"YAML parsing failed: {str(e)}"}
    
    def get_requirements_table(self, yaml_content: str) -> Tuple[bool, pd.DataFrame]:
        """Extract requirements table from YAML csv_schema."""
        success, yaml_data = self.parse_yaml_content(yaml_content)
        
        if not success:
            return False, None
            
        try:
            # Look for csv_schema at root level or nested under first key
            csv_schema = None
            
            if isinstance(yaml_data, dict):
                if 'csv_schema' in yaml_data:
                    csv_schema = yaml_data['csv_schema']
                else:
                    # Check nested structure - look in first level values
                    for key, value in yaml_data.items():
                        if isinstance(value, dict) and 'csv_schema' in value:
                            csv_schema = value['csv_schema']
                            break
            
            if csv_schema and 'rows' in csv_schema and isinstance(csv_schema['rows'], list):
                rows_data = []
                
                # Use pretty column names if available, otherwise machine names
                columns = csv_schema.get('columns_pretty', csv_schema.get('columns', []))
                
                for row in csv_schema['rows']:
                    if isinstance(row, dict):
                        # Create a row using the original structure from csv_schema
                        row_dict = {}
                        
                        # Map fields from the actual row data
                        for i, column in enumerate(columns):
                            # Try to get value from row using different possible keys
                            value = None
                            for key in row.keys():
                                if key == column or str(key).lower() == str(column).lower():
                                    value = row[key]
                                    break
                            
                            # If no direct match, try to map based on position or common patterns
                            if value is None:
                                row_values = list(row.values())
                                if i < len(row_values):
                                    value = row_values[i]
                                else:
                                    value = 'N/A'
                            
                            row_dict[column] = value
                        
                        rows_data.append(row_dict)
                
                if rows_data:
                    requirements_df = pd.DataFrame(rows_data)
                    
                    # Fix mixed data types to prevent PyArrow serialization errors
                    for col in requirements_df.columns:
                        requirements_df[col] = requirements_df[col].astype(str)
                    
                    # Replace pandas NaN representations with empty strings
                    requirements_df = requirements_df.replace(['nan', 'None', 'NaN'], '', regex=False)
                    
                    return True, requirements_df
                else:
                    return False, None
            else:
                return False, None
                
        except Exception as e:
            print(f"Error parsing requirements table: {e}")
            return False, None
                
        except Exception as e:
            return False, None
    
    def get_yaml_preview_info(self, yaml_content: str) -> Dict[str, Any]:
        """Get comprehensive YAML preview information."""
        success, yaml_data = self.parse_yaml_content(yaml_content)
        
        preview_info = {
            'raw_content': yaml_content,
            'parsed_successfully': success,
            'has_csv_schema': False,
            'csv_schema_info': None,
            'requirements_table': None,
            'column_headers': None
        }
        
        if success and isinstance(yaml_data, dict):
            # Look for csv_schema at root level or nested under first key
            csv_schema = None
            
            if 'csv_schema' in yaml_data:
                csv_schema = yaml_data['csv_schema']
            else:
                # Check nested structure - look in first level values
                for key, value in yaml_data.items():
                    if isinstance(value, dict) and 'csv_schema' in value:
                        csv_schema = value['csv_schema']
                        break
            
            if csv_schema:
                preview_info['has_csv_schema'] = True
                preview_info['csv_schema_info'] = csv_schema
                
                # Get requirements table
                table_success, requirements_df = self.get_requirements_table(yaml_content)
                if table_success:
                    preview_info['requirements_table'] = requirements_df
                
                # Get column headers
                if 'columns' in csv_schema:
                    preview_info['column_headers'] = csv_schema['columns']
                elif 'columns_pretty' in csv_schema:
                    preview_info['column_headers'] = csv_schema['columns_pretty']
        
        return preview_info
    
    def display_comparison(self, requirements_df: pd.DataFrame, extracted_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Helper method to prepare comparison data for display."""
        return {
            'original_requirements': requirements_df,
            'ai_extracted': extracted_df
        }
    
    def process_yaml_file(self, yaml_content: str, api_key: str = None) -> Dict[str, Any]:
        """Complete Step 1 processing: preview, extract, and prepare results."""
        result = {
            'preview_info': self.get_yaml_preview_info(yaml_content),
            'extraction_success': False,
            'extracted_parameters': None,
            'comparison_data': None,
            'error': None
        }
        
        # If API key provided, also do extraction
        if api_key:
            try:
                success, extraction_result = self.extract_parameters(yaml_content, api_key)
                result['extraction_success'] = success
                
                if success:
                    result['extracted_parameters'] = extraction_result
                    
                    # Prepare comparison if we have original requirements
                    if result['preview_info']['requirements_table'] is not None:
                        result['comparison_data'] = self.display_comparison(
                            result['preview_info']['requirements_table'],
                            extraction_result['parameters_df']
                        )
                else:
                    result['error'] = extraction_result.get('error')
                    
            except Exception as e:
                result['error'] = f"Processing error: {str(e)}"
        
        return result
    
    # =================== STREAMLIT UI METHODS ===================
    
    def render_step1_ui(self, st, model: str, api_key: str, get_agent_prompts_func) -> None:
        """Complete Step 1 UI rendering - consolidates all Step 1 logic from app.py"""
        
        # Step 1: YAML Parameter Extraction
        st.subheader("Step 1: Upload YAML Requirements")
        st.markdown("*Upload your YAML requirements file to extract compliance parameters*")
        
        yaml_file = st.file_uploader(
            "Choose YAML file",
            type=['yaml', 'yml'],
            key="yaml_uploader",
            help="Upload your 2.10_HS_Beneath_Staircase.yaml or similar compliance YAML file"
        )
        
        if yaml_file:
            self._handle_yaml_upload(st, yaml_file)
        
        # Display Requirements Table and handle extraction
        self._render_requirements_table_and_extraction(st, model, api_key, get_agent_prompts_func)
        
        # Display AI results
        self._render_ai_results(st)
    
    def _handle_yaml_upload(self, st, yaml_file) -> None:
        """Handle YAML file upload and preview"""
        st.success(f"✅ File uploaded: {yaml_file.name} ({len(yaml_file.getvalue())} bytes)")
        
        # Store YAML content for processing
        yaml_content = yaml_file.getvalue().decode('utf-8')
        st.session_state.yaml_content = yaml_content
        
        # Get preview info
        preview_info = self.get_yaml_preview_info(yaml_content)
        
        # Show preview with structured table
        with st.expander("📄 YAML Content Preview", expanded=False):
            self._render_yaml_preview(st, preview_info)
        
        # Store requirements table for later use
        if preview_info['has_csv_schema'] and preview_info['requirements_table'] is not None:
            st.session_state.requirements_df = preview_info['requirements_table']
            st.session_state.has_requirements_table = True
        else:
            st.session_state.has_requirements_table = False
    
    def _render_yaml_preview(self, st, preview_info: Dict[str, Any]) -> None:
        """Render YAML preview content"""
        # Try to display structured csv_schema as table
        if preview_info['has_csv_schema']:
            st.subheader("📊 CSV Schema Table Structure")
            
            if preview_info['requirements_table'] is not None:
                st.dataframe(preview_info['requirements_table'], use_container_width=True, hide_index=True)
                st.caption("**7) CSV-structured table (for export/import)** - Requirements table from YAML csv_schema")
            else:
                st.info("No valid row data found in csv_schema")
                
            # Show column headers if available
            if preview_info['column_headers']:
                st.subheader("📋 Column Headers")
                if isinstance(preview_info['column_headers'], list):
                    st.write(", ".join([str(col) for col in preview_info['column_headers']]))
                else:
                    st.write(preview_info['column_headers'])
        else:
            st.info("No csv_schema found in YAML.")
            
            # Show a compact YAML summary instead of raw content
            raw_content = preview_info['raw_content']
            lines = raw_content.split('\n')
            summary_lines = lines[:10] if len(lines) > 10 else lines
            summary_content = '\n'.join(summary_lines)
            if len(lines) > 10:
                summary_content += f"\n... ({len(lines) - 10} more lines)"
            
            with st.expander("📄 YAML Summary", expanded=False):
                st.text_area("YAML Content Summary", summary_content, height=150)
    
    def _render_requirements_table_and_extraction(self, st, model: str, api_key: str, get_agent_prompts_func) -> None:
        """Render extraction button and handle extraction"""
        
        # Show extract button if we have YAML content
        if st.session_state.get('yaml_content'):
            if st.session_state.get('has_requirements_table', False):
                # We have a structured table - show extraction button
                if st.button("🔍 Extract Parameters", key="extract_params", use_container_width=True):
                    self._execute_extraction(st, model, api_key, get_agent_prompts_func)
            else:
                # If we have YAML but no requirements table, show a message and still allow extraction
                st.info("💡 **Upload a YAML file with csv_schema structure for optimal results**")
                
                if st.button("🔍 Extract Parameters (Direct)", key="extract_params_direct", use_container_width=True):
                    self._execute_extraction(st, model, api_key, get_agent_prompts_func)
    
    def _execute_extraction(self, st, model: str, api_key: str, get_agent_prompts_func) -> None:
        """Execute parameter extraction process"""
        with st.spinner("Step 1: Extracting parameters from YAML..."):
            try:
                # Get custom prompts
                prompts = get_agent_prompts_func()
                
                # Initialize Agent 1 with custom prompts
                agent1 = YAMLParameterExtractor(model=model)
                
                # Set custom prompts if agent supports it
                if hasattr(agent1, 'set_prompts'):
                    agent1.set_prompts(prompts['agent1_yaml_extractor'])
                
                # Use stored YAML content
                yaml_content = st.session_state.get('yaml_content', '')
                if not yaml_content:
                    st.error("❌ No YAML content found. Please upload a YAML file first.")
                    st.stop()
                
                # Extract parameters
                success, result = agent1.extract_parameters(yaml_content, api_key)
                
                if success:
                    st.session_state.parameters_df = result['parameters_df']
                    st.session_state.step1_completed = True
                    
                    # Store component analysis data if available
                    if 'components_detected' in result:
                        st.session_state.components_detected = result['components_detected']
                    if 'observed_count' in result:
                        st.session_state.observed_count = result['observed_count']
                    if 'suggested_count' in result:
                        st.session_state.suggested_count = result['suggested_count']
                    
                    # Show success message with component details
                    components_msg = ""
                    if result.get('components_detected'):
                        components_msg = f" | Components: {', '.join(result['components_detected'][:3])}"
                        if len(result['components_detected']) > 3:
                            components_msg += "..."
                    
                    st.success(f"✅ Component analysis completed using {result.get('method', 'AI')} method{components_msg}")
                else:
                    st.error(f"❌ Parameter extraction failed: {result.get('error')}")
                    
            except Exception as e:
                st.error(f"❌ Extraction error: {str(e)}")
    
    def _render_ai_results(self, st) -> None:
        """Render AI extraction results with editable parameters"""
        # Display AI-extracted parameters if Step 1 completed
        if st.session_state.step1_completed and st.session_state.parameters_df is not None:
            st.markdown("---")
            st.subheader("🎯 Parameters Detection (Step 1)")
            
            # Show component detection summary if available
            if hasattr(st.session_state, 'components_detected') and st.session_state.components_detected:
                st.caption("**🏗️ Building Components Detected:** " + ", ".join(st.session_state.components_detected))
            
            # Show extraction counts - calculate from actual data
            df = st.session_state.parameters_df
            
            # First clean the data to remove placeholders
            clean_df = df[
                ~df['parameter'].str.contains('placeholder_', na=False) &
                df['parameter'].notna() &
                (df['parameter'] != "") &
                (df['parameter'] != "None")
            ]
            
            # Count observed parameters (those with YAML references, not suggested)
            observed_mask = (
                (clean_df['reference'].str.contains('YAML:', na=False)) | 
                (clean_df['reference'].str.contains('CSV Row', na=False)) |
                (clean_df['reference'].str.contains('Clause:', na=False))
            ) & (~clean_df['reference'].str.contains('Suggested', na=False))
            
            observed_count = len(clean_df[observed_mask])
            
            # Count suggested parameters (those explicitly marked as suggested)
            suggested_count = len(clean_df[clean_df['reference'].str.contains('Suggested', na=False)])
            
            # Count total clean parameters
            total_count = len(clean_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Observed Parameters", observed_count, help="Parameters found with YAML evidence")
            with col2:
                st.metric("💡 Suggested Parameters", suggested_count, help="Additional parameters typical for detected components")
            with col3:
                st.metric("🎯 Total Parameters", total_count, help="Combined for Step 2 analysis")
            
            st.caption("**AI Analysis:** Evidence-based parameter extraction with component-aware suggestions")
            
            # Show AI results with editable data editor
            st.markdown("**📝 Edit Parameters (Click cells to modify, add/remove rows and columns):**")
            with st.container():
                # Clean the dataframe before displaying to ensure no unwanted columns
                canonical_columns = ["no", "reference", "parameter", "value", "unit", "type", "description"]
                display_df = st.session_state.parameters_df.copy()
                
                # Remove any unwanted columns (including any "false" columns, checkbox columns)
                columns_to_keep = []
                for col in display_df.columns:
                    if col in canonical_columns:
                        columns_to_keep.append(col)
                
                # Keep only canonical columns
                display_df = display_df[columns_to_keep] if columns_to_keep else pd.DataFrame(columns=canonical_columns)
                
                # Remove placeholder rows aggressively
                if not display_df.empty:
                    display_df = display_df[
                        ~display_df['parameter'].str.contains('placeholder_', na=False) &
                        display_df['parameter'].notna() &
                        (display_df['parameter'] != "") &
                        (display_df['parameter'] != "None")
                    ]
                
                # Ensure canonical columns exist
                for col in canonical_columns:
                    if col not in display_df.columns:
                        display_df[col] = ""
                
                # Reorder columns to canonical order and renumber
                display_df = display_df[canonical_columns]
                if len(display_df) > 0:
                    display_df["no"] = range(1, len(display_df) + 1)
                
                # Use data_editor for editable parameters
                edited_df = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,  # Hide pandas row index numbers
                    num_rows="dynamic",  # Allow adding/removing rows
                    column_order=canonical_columns,  # Enforce column order
                    column_config={
                        "no": st.column_config.NumberColumn("No.", disabled=False, min_value=1),
                        "reference": st.column_config.TextColumn("Reference", help="YAML reference"),
                        "parameter": st.column_config.TextColumn("Parameter", help="Parameter name"),
                        "value": st.column_config.TextColumn("Value", help="Parameter value"),
                        "unit": st.column_config.TextColumn("Unit", help="Unit of measurement"),
                        "type": st.column_config.TextColumn("Type", help="Component type"),
                        "description": st.column_config.TextColumn("Description", help="Parameter description")
                    },
                    disabled=False,  # Enable editing
                    key="parameters_editor"
                )
                
                # Update session state with edited data, ensuring only canonical columns
                if not edited_df.equals(st.session_state.parameters_df):
                    # Filter to only include canonical columns and remove any unwanted columns
                    canonical_columns = ["no", "reference", "parameter", "value", "unit", "type", "description"]
                    
                    # Keep only canonical columns that exist in the edited dataframe
                    filtered_columns = [col for col in canonical_columns if col in edited_df.columns]
                    cleaned_df = edited_df[filtered_columns].copy()
                    
                    # Remove any columns with boolean values or "false" in the name
                    for col in cleaned_df.columns:
                        if col.lower() == 'false' or str(col).lower().startswith('false'):
                            cleaned_df = cleaned_df.drop(columns=[col])
                    
                    st.session_state.parameters_df = cleaned_df
                
                # Show extraction method info
                st.info("""
                ℹ️ **Component-Based AI Processing:** 
                - **Observed**: Parameters with direct YAML evidence (csv_schema, parameter_templates, etc.)
                - **Suggested**: Additional parameters typical for detected building components
                - **Fully Editable**: 
                  * Click cells to edit values
                  * Add/remove rows using the row controls
                  * Row index numbers shown for easy reference
                  * All changes automatically saved to session
                """)
            
            # Save and proceed button
            if st.button(
                "💾 Save parameters.csv and proceed to drawing analysis",
                key="save_and_proceed_step1",
                use_container_width=True,
                type="primary"
            ):
                # Update row numbering
                if len(st.session_state.parameters_df) > 0:
                    st.session_state.parameters_df["no"] = range(1, len(st.session_state.parameters_df) + 1)
                
                # Save to CSV (optional - for persistent storage)
                csv_path = "parameters.csv"
                st.session_state.parameters_df.to_csv(csv_path, index=False)
                
                st.success(f"✅ Parameters saved! Ready for Step 2 - Drawing Analysis ({len(st.session_state.parameters_df)} parameters)")
                st.info("👉 **Next:** Upload your technical drawings in Step 2 to analyze compliance against these parameters.")
                
                # Auto-scroll to Step 2 (if it exists)
                st.rerun()
    
    def _render_step2_analysis_insights(self, st) -> None:
        """Render Step 2 analysis insights based on extracted parameters"""
        st.info("**Analysis Complete:** The following parameters have been identified as search variables for Step 2 technical drawing analysis:")
        
        # Categorize parameters for drawing search guidance
        df = st.session_state.parameters_df
        
        # Extract parameter types from the dataframe
        area_params = []
        dimension_params = []
        volume_params = []
        other_params = []
        
        for _, row in df.iterrows():
            param_name = str(row.iloc[0])  # First column contains parameter names
            param_value = str(row.iloc[1]) if len(row) > 1 else ""  # Second column contains values
            
            if 'area' in param_name.lower() or 'm²' in param_value:
                area_params.append(f"• **{param_name}**: {param_value}")
            elif 'height' in param_name.lower() or 'width' in param_name.lower() or 'depth' in param_name.lower() or 'mm' in param_value or 'm' in param_value:
                dimension_params.append(f"• **{param_name}**: {param_value}")
            elif 'volume' in param_name.lower() or 'm³' in param_value:
                volume_params.append(f"• **{param_name}**: {param_value}")
            else:
                other_params.append(f"• **{param_name}**: {param_value}")
        
        # Display categorized parameters
        col1, col2 = st.columns(2)
        
        with col1:
            if area_params:
                st.markdown("**🏠 Area Requirements** (Search for: floor plans, area calculations)")
                for param in area_params:
                    st.markdown(param)
            
            if dimension_params:
                st.markdown("**📏 Dimensional Requirements** (Search for: sections, elevations, details)")
                for param in dimension_params:
                    st.markdown(param)
        
        with col2:
            if volume_params:
                st.markdown("**📦 Volume Requirements** (Search for: 3D views, space calculations)")
                for param in volume_params:
                    st.markdown(param)
            
            if other_params:
                st.markdown("**⚙️ Other Requirements** (Search for: specifications, notes)")
                for param in other_params:
                    st.markdown(param)
        
        st.markdown("---")
        st.markdown("**🎯 Step 2 Search Strategy:**")
        st.markdown("""
        1. **Area parameters** → Look for floor plans and GFA calculations
        2. **Dimensional parameters** → Search building sections and elevation drawings  
        3. **Volume parameters** → Find 3D views and space volume calculations
        4. **Other requirements** → Check specification sheets and construction notes
        """)
        
        st.success("✅ Ready for Step 2: Upload technical drawings to search for these parameter values")
        
    def extract_parameters(self, yaml_content: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Extract parameters from YAML content using AI first, with fallback to direct extraction."""
        
        # Check provider selection first to determine if we should try AI extraction
        provider = 'OpenAI'  # default
        try:
            import streamlit as st
            provider = getattr(st.session_state, 'ai_provider', 'OpenAI')
        except:
            pass
        
        print(f"DEBUG: Main extract method - provider: {provider}, "
              f"api_key provided: {bool(api_key)}")
        
        # Try AI extraction if we have an API key OR if using Ollama (which doesn't need API key)
        if api_key or provider == "Ollama":
            try:
                ai_success, ai_result = self._extract_with_ai(yaml_content, api_key)
                if ai_success:
                    return ai_success, ai_result
                else:
                    # AI failed, try direct extraction as fallback
                    print(f"AI extraction failed: {ai_result.get('error')}")
            except Exception as e:
                print(f"AI extraction error: {str(e)}")
        else:
            print(f"DEBUG: Skipping AI extraction - no API key and not Ollama")
        
        # Fallback to direct extraction from csv_schema
        return self._extract_direct_from_csv_schema(yaml_content)
    
    def _extract_with_ai(self, yaml_content: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Extract parameters using AI prompt-response approach with multi-provider support."""
        
        prompt = self.prompt.format(yaml_content=yaml_content)
        
        try:
            # Get provider from session state or use OpenAI as default
            try:
                import streamlit as st
                # Check all session state for debugging
                print(f"DEBUG: All session state keys: {list(st.session_state.keys())}")
                
                provider = getattr(st.session_state, 'ai_provider', 'OpenAI')
                print(f"DEBUG: Selected provider from session: {provider}")
                
                # Also check if there are other provider-related keys
                for key in st.session_state.keys():
                    if 'provider' in key.lower():
                        print(f"DEBUG: Session state {key}: {st.session_state[key]}")
                
                # Get the correct API key for the selected provider
                if provider == "OpenAI":
                    correct_api_key = st.secrets.get("openai", {}).get("api_key") or api_key
                elif provider == "GovTech":
                    correct_api_key = st.secrets.get("govtech", {}).get("api_key") or api_key
                elif provider == "Ollama":
                    correct_api_key = None  # Ollama doesn't need API key
                else:
                    correct_api_key = api_key
                
                print(f"DEBUG: Using provider: {provider}, API key type: {'None' if not correct_api_key else correct_api_key[:10] + '...'}")
                    
            except Exception as e:
                print(f"DEBUG: Error getting provider from session: {str(e)}")
                provider = 'OpenAI'  # Default if streamlit not available
                correct_api_key = api_key
            
            # Call the appropriate provider method
            print(f"DEBUG: Calling provider method for: {provider}")
            print(f"DEBUG: Provider comparison - provider == 'OpenAI': {provider == 'OpenAI'}")
            print(f"DEBUG: Provider comparison - provider == 'GovTech': {provider == 'GovTech'}")
            print(f"DEBUG: Provider comparison - provider == 'Ollama': {provider == 'Ollama'}")
            if provider == "OpenAI":
                result = self._call_openai(prompt, correct_api_key)
            elif provider == "GovTech":
                result = self._call_govtech(prompt, correct_api_key)
            elif provider == "Ollama":
                result = self._call_ollama(prompt, correct_api_key)
            else:
                # Default to OpenAI if unknown provider
                print(f"DEBUG: Unknown provider {provider}, defaulting to OpenAI")
                result = self._call_openai(prompt, correct_api_key)
            
            # Extract the content from the provider response
            content = ""
            if "error" in result:
                return False, {"error": f"AI provider error: {result['error']}"}
            
            # Handle different response formats from different providers
            if provider == "Ollama":
                # Ollama returns {"response": "content"}
                content = result.get("response", "")
            elif provider in ["OpenAI", "GovTech"]:
                # OpenAI and GovTech return {"choices": [{"message": {"content": "..."}}]}
                if "choices" in result and result["choices"]:
                    content = result["choices"][0]["message"]["content"].strip()
                else:
                    # Fallback - sometimes GovTech might return different format
                    content = str(result)
            else:
                # Generic fallback
                if "choices" in result and result["choices"]:
                    content = result["choices"][0]["message"]["content"].strip()
                elif "response" in result:
                    content = result["response"]
                else:
                    content = str(result)
            
            if not content:
                return False, {"error": "Empty response from AI provider"}

            # Try to clean and parse JSON response
            data = self._parse_ai_response(content)
            if data is None:
                return False, {"error": f"Could not parse AI response as JSON. Response: {content[:500]}..."}
            
            # Get the original requirements table for reference mapping
            table_success, requirements_df = self.get_requirements_table(yaml_content)
            reference_mapping = {}
            
            if table_success and requirements_df is not None:
                # Create a mapping from parameter names to CSV schema references
                for idx, row in requirements_df.iterrows():
                    if 'parameter' in row and pd.notna(row['parameter']):
                        param_name = str(row['parameter']).lower()
                        # Create reference using row number and parameter name from original CSV
                        csv_ref = f"CSV Row {idx + 1}: {row.get('parameter', 'N/A')}"
                        reference_mapping[param_name] = csv_ref
                    
                    # Also map by other potential column names that might contain parameters
                    for col in row.index:
                        if pd.notna(row[col]) and str(col).lower() in ['requirement', 'item', 'description']:
                            param_text = str(row[col]).lower()
                            csv_ref = f"CSV Row {idx + 1}: {col}"
                            reference_mapping[param_text] = csv_ref
            
            # Handle new component-based format
            observed_params = data.get("observed", [])
            suggested_params = data.get("suggested", [])
            components_detected = data.get("components_detected", [])
            
            if not observed_params and not suggested_params:
                return False, {"error": "No parameters extracted from AI response"}
            
            # Convert observed parameters to display format
            parameters = []
            for i, param in enumerate(observed_params, 1):
                # Try to find CSV schema reference for this parameter
                param_name_key = param.get("canonical_parameter", param.get("original_parameter", "")).lower()
                csv_reference = "N/A"
                
                # Look for exact or partial matches in CSV schema
                for ref_key, ref_value in reference_mapping.items():
                    if param_name_key in ref_key or ref_key in param_name_key:
                        csv_reference = ref_value
                        break
                
                # If no CSV match found, try to use provenance information
                if csv_reference == "N/A":
                    provenance = param.get("provenance", {})
                    yaml_section = provenance.get("yaml_section", "")
                    field_name = provenance.get("field_name", "")
                    if yaml_section and field_name:
                        csv_reference = f"YAML: {yaml_section}.{field_name}"
                    elif param.get("clause"):
                        csv_reference = f"Clause: {param.get('clause')}"
                
                parameters.append({
                    "no": i,
                    "reference": csv_reference,
                    "parameter": param.get("canonical_parameter", param.get("original_parameter", "N/A")),
                    "value": param.get("value", "N/A"),
                    "unit": param.get("unit", "N/A"), 
                    "type": param.get("component", "N/A"),
                    "description": f"Component: {param.get('component', 'N/A')} | Evidence: {param.get('provenance', {}).get('evidence_text', 'N/A')[:50]}..."
                })
            
            # Add suggested parameters as additional context
            for i, param in enumerate(suggested_params, len(parameters) + 1):
                parameters.append({
                    "no": i,
                    "reference": "Suggested (No CSV source)",
                    "parameter": param.get("parameter", "N/A"),
                    "value": "TBD", 
                    "unit": "N/A",
                    "type": param.get("component", "N/A"),
                    "description": f"Suggested: {param.get('reason', 'N/A')}"
                })
            
            # Convert to DataFrame and normalize
            df = pd.DataFrame(parameters)
            df_normalized = self._normalize_to_9x7(df)
            
            # Save to CSV
            csv_path = "parameters.csv"
            df_normalized.to_csv(csv_path, index=False)
            
            return True, {
                "parameters_df": df_normalized,
                "parameters_csv": csv_path,
                "components_detected": components_detected,
                "observed_count": len(observed_params),
                "suggested_count": len(suggested_params),
                "method": "AI"
            }
                
        except Exception as e:
            return False, {"error": f"AI extraction failed: {str(e)}"}
    
    def _is_valid_parameter_data(self, data: Any) -> bool:
        """Check if data is valid parameter structure"""
        if not isinstance(data, dict):
            return False
        return "observed" in data or "suggested" in data
    
    def _call_openai(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            if not api_key:
                return {"error": "OpenAI API key is required"}
            
            # Debug: Check API key format (remove this after testing)
            print(f"DEBUG: OpenAI API key starts with: {api_key[:10]}..." if api_key else "DEBUG: No API key provided")
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 2000
                },
                timeout=30  # Reduced timeout for faster testing
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"OpenAI API error: {str(e)}"}
    
    def _call_govtech(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """Call GovTech LLMaaS API"""
        try:
            if not api_key:
                return {"error": "GovTech API key is required"}
            
            # Debug: Check API key format (remove this after testing)
            print(f"DEBUG: GovTech API key starts with: {api_key[:10]}..." if api_key else "DEBUG: No GovTech API key")
            
            # Use the correct GovTech model - they might not support gpt-4o
            model = self.model if self.model in ["gpt-4", "gpt-4o", "gpt-3.5-turbo"] else "gpt-4"
            
            response = requests.post(
                "https://llmaas.govtext.gov.sg/gateway/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 2000
                },
                timeout=30  # Reduced timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"GovTech API error: {str(e)}"}
    
    def _call_ollama(self, prompt: str, api_key: str) -> Dict[str, Any]:
        """Call Ollama local API"""
        try:
            # Debug: Check Ollama call
            print(f"DEBUG: Attempting Ollama call with model: {self.model}")
            
            # Use the correct Ollama model format
            model = self.model if self.model in ["llama3.2:latest", "llama3.1:latest", "llama3:latest"] else "llama3.2:latest"
            print(f"DEBUG: Using Ollama model: {model}")
            
            # First test if Ollama is available
            test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if test_response.status_code != 200:
                return {"error": "Ollama service not accessible. Please ensure Ollama is running on localhost:11434"}
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            print(f"DEBUG: Sending request to Ollama with payload keys: {list(payload.keys())}")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60  # Ollama can be slow
            )
            
            print(f"DEBUG: Ollama response status: {response.status_code}")
            
            response.raise_for_status()
            
            result = response.json()
            
            # Debug: Check Ollama response format
            print(f"DEBUG: Ollama response keys: {list(result.keys())}")
            if "response" in result:
                print(f"DEBUG: Ollama response content length: {len(result['response'])}")
            
            # Return in consistent format for our parser
            return {
                "response": result.get("response", "")
            }
        except requests.exceptions.ConnectionError as e:
            return {"error": f"Ollama connection error: Cannot connect to localhost:11434. Is Ollama running? {str(e)}"}
        except requests.exceptions.Timeout as e:
            return {"error": f"Ollama timeout error: {str(e)}"}
        except Exception as e:
            return {"error": f"Ollama API error: {str(e)}"}

    def _parse_ai_response(self, content: str) -> dict:
        """Parse AI response with multiple strategies"""
        try:
            # First try direct parsing
            return json.loads(content)
        except json.JSONDecodeError:
            pass
            
        try:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_content = json_match.group(1).strip()
                return json.loads(json_content)
        except (json.JSONDecodeError, AttributeError):
            pass
            
        try:
            # Try to find JSON-like content between { and }
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_content = json_match.group(0)
                return json.loads(json_content)
        except (json.JSONDecodeError, AttributeError):
            pass
            
        return None

    def _extract_direct_from_csv_schema(self, yaml_content: str) -> Tuple[bool, Dict[str, Any]]:
        """Extract parameters directly from YAML csv_schema as fallback."""
        try:
            # Get requirements table
            table_success, requirements_df = self.get_requirements_table(yaml_content)
            
            if not table_success or requirements_df is None:
                return False, {"error": "No csv_schema found in YAML for direct extraction"}
            
            # Normalize the requirements table to 9x7 format
            df_normalized = self._normalize_to_9x7(requirements_df)
            
            # Save to CSV
            csv_path = "parameters.csv"
            df_normalized.to_csv(csv_path, index=False)
            
            return True, {
                "parameters_df": df_normalized,
                "parameters_csv": csv_path,
                "method": "Direct"
            }
            
        except Exception as e:
            return False, {"error": f"Direct extraction failed: {str(e)}"}
    
    def _normalize_to_9x7(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame to exactly 9 rows × 7 columns with fixed structure."""
        canonical_columns = ["no", "reference", "parameter", "value", "unit", "type", "description"]
        
        # Ensure all columns exist
        for col in canonical_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Select only canonical columns
        df = df[canonical_columns].copy()
        
        # Remove rows that are just placeholders (empty or placeholder parameters)
        df = df[~df['parameter'].str.contains('placeholder_', na=False)]
        df = df[df['parameter'].notna() & (df['parameter'] != "")]
        
        # NO LONGER enforce exactly 9 rows - show only actual parameters
        if len(df) > 9:
            df = df.head(9)
        
        # Ensure 'no' column is sequential starting from 1
        if len(df) > 0:
            df["no"] = range(1, len(df) + 1)
        
        # Fix data types to prevent PyArrow serialization errors
        # Convert all columns to string first to handle mixed types
        df = df.astype(str)
        
        # Then convert 'no' column to integer
        df["no"] = pd.to_numeric(df["no"], errors='coerce').fillna(0).astype(int)
        
        # Replace pandas NaN representations with empty strings
        df = df.replace(['nan', 'None', 'NaN'], '', regex=False)
        
        return df