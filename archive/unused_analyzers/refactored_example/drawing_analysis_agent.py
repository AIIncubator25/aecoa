"""
Main Drawing Analysis Agent (Refactored)
Orchestrates the drawing analysis process using specialized components.
"""
from typing import Dict, Any, List, Tuple
from pathlib import Path

from .compliance_config import ComplianceConfigManager
from .file_handler import DrawingFileHandler  
from .data_processor import DataProcessor
from .api_client import APIClient
from ..utils.prompt_manager import load_agent_prompts


class DrawingAnalysisAgent:
    """
    Refactored Drawing Analysis Agent with separated concerns.
    This is the main orchestrator that coordinates specialized components.
    """
    
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        # Initialize specialized components
        self.config_manager = ComplianceConfigManager()
        self.file_handler = DrawingFileHandler()
        self.data_processor = DataProcessor(self.config_manager)
        self.api_client = APIClient(provider, model)
        
        # Load prompts
        self.prompt = load_agent_prompts("agent2")
        
        # Basic properties
        self.provider = provider
        self.model = model
    
    # ==== CONFIGURATION METHODS ====
    
    def set_compliance_domain(self, domain: str) -> bool:
        """Set the compliance domain for analysis."""
        return self.config_manager.set_compliance_domain(domain)
    
    def set_hs_scenario(self, scenario_name: str) -> bool:
        """Set the HS scenario for analysis."""
        return self.config_manager.set_hs_scenario(scenario_name)
    
    def set_intelligent_mode(self, use_intelligent: bool = True) -> None:
        """Switch to intelligent AI-focused analysis mode."""
        if use_intelligent:
            try:
                # Try to load intelligent prompts
                project_root = Path(__file__).parent.parent.parent.parent
                hs_system_path = project_root / 'prompts' / 'agent2_hs_system.txt'
                hs_user_path = project_root / 'prompts' / 'agent2_hs_user.txt'
                
                if hs_system_path.exists() and hs_user_path.exists():
                    with open(hs_system_path, 'r', encoding='utf-8') as file:
                        system_prompt = file.read()
                    with open(hs_user_path, 'r', encoding='utf-8') as file:
                        user_prompt = file.read()
                    print("[DEBUG] Using HS-specific intelligent prompts")
                else:
                    # Fallback to generic intelligent prompts
                    system_path = project_root / 'prompts' / 'agent2_intelligent_system.txt'
                    user_path = project_root / 'prompts' / 'agent2_intelligent_user.txt'
                    
                    with open(system_path, 'r', encoding='utf-8') as file:
                        system_prompt = file.read()
                    with open(user_path, 'r', encoding='utf-8') as file:
                        user_prompt = file.read()
                    print("[DEBUG] Using generic intelligent prompts")
                
                self.prompt = {"system": system_prompt, "user": user_prompt}
                print("[DEBUG] Switched to intelligent AI-focused mode")
                
            except Exception as exception:
                print(f"[WARNING] Could not load intelligent prompts: {exception}")
                print("[DEBUG] Continuing with default prompts")
        else:
            self.prompt = load_agent_prompts("agent2")
    
    def set_prompts(self, prompts: Dict[str, str]) -> None:
        """Set custom prompts for the agent."""
        if "user" in prompts:
            default_prompts = load_agent_prompts("agent2")
            self.prompt = {
                "system": prompts.get("system", default_prompts["system"]),
                "user": prompts["user"]
            }
        else:
            self.prompt = prompts
    
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent."""
        return load_agent_prompts("agent2")
    
    # ==== FILE PROCESSING METHODS ====
    
    def get_file_summary(self, drawing_files: List) -> Dict[str, Any]:
        """Get summary information about uploaded drawing files."""
        return self.file_handler.get_file_summary(drawing_files)
    
    def save_uploaded_files(self, drawing_files: List, upload_dir: str = "uploads") -> List[str]:
        """Save uploaded files to local directory and return file paths."""
        return self.file_handler.save_uploaded_files(drawing_files, upload_dir)
    
    def extract_dxf_text(self, dxf_file_path: str) -> str:
        """Extract text content from DXF files."""
        return self.file_handler.extract_dxf_text(dxf_file_path)
    
    # ==== ANALYSIS METHODS ====
    
    def analyze_drawings(self, image_paths: List[str], parameters_file_path: str, 
                        api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Main analysis method that orchestrates the drawing analysis process.
        """
        if not api_key:
            return False, {"error": "API key is required for AI analysis"}
        
        try:
            # Load parameters
            if not Path(parameters_file_path).exists():
                return False, {"error": f"Parameters file not found: {parameters_file_path}"}
            
            if parameters_file_path.endswith('.json'):
                parameters_df = self.data_processor.load_parameters_from_json(parameters_file_path)
            else:
                import pandas as pd
                parameters_df = pd.read_csv(parameters_file_path)
            
            # Separate image and DXF files
            valid_images = [p for p in image_paths 
                           if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
            dxf_files = [p for p in image_paths if p.lower().endswith('.dxf')]
            
            if not valid_images:
                return False, {"error": "No valid image files (JPG/PNG) provided"}
            
            # Perform AI analysis
            return self._perform_ai_analysis(parameters_df, valid_images, dxf_files, api_key)
            
        except Exception as exception:
            return False, {"error": f"Drawing analysis failed: {str(exception)}"}
    
    def _perform_ai_analysis(self, parameters_df, valid_images: List[str], 
                           dxf_files: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Perform the actual AI analysis."""
        # Prepare context
        param_context = self._prepare_parameter_context(parameters_df)
        drawing_list = [Path(p).name for p in valid_images]
        dxf_text_content = self._extract_all_dxf_text(dxf_files)
        
        # Format user prompt
        user_prompt = self._format_user_prompt(param_context, drawing_list, dxf_text_content)
        
        # Call AI API
        success, result = self.api_client.analyze_with_ai(
            self.prompt["system"], user_prompt, valid_images, api_key
        )
        
        if not success:
            return False, result
        
        # Parse response
        content = result.get('content', '')
        return self._parse_and_process_response(content, parameters_df, valid_images, dxf_files)
    
    def _prepare_parameter_context(self, parameters_df) -> str:
        """Prepare parameter context for AI prompt."""
        param_rows = []
        for _, row in parameters_df.iterrows():
            param_rows.append(
                f"{row['parameter']}: {row['description']} "
                f"(required: {row['value']} {row['unit']})"
            )
        return "\n".join(param_rows)
    
    def _extract_all_dxf_text(self, dxf_files: List[str]) -> str:
        """Extract text from all DXF files."""
        dxf_text_content = []
        for dxf_file in dxf_files:
            dxf_text = self.file_handler.extract_dxf_text(dxf_file)
            if (dxf_text and not dxf_text.startswith("Error") 
                and not dxf_text.startswith("No text content")):
                dxf_text_content.append(f"=== DXF FILE: {Path(dxf_file).name} ===")
                dxf_text_content.append(dxf_text)
                dxf_text_content.append("")
        
        return "\n".join(dxf_text_content) if dxf_text_content else "No DXF text content available"
    
    def _format_user_prompt(self, param_context: str, drawing_list: List[str], 
                          dxf_text_content: str) -> str:
        """Format the user prompt with context."""
        try:
            # Try HS-specific format first
            return self.prompt["user"].format(
                param_context=param_context,
                drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                dxf_content=dxf_text_content,
            )
        except KeyError:
            try:
                # Try generic format
                return self.prompt["user"].format(
                    param_context=param_context,
                    drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                    dxf_text=dxf_text_content,
                    hints="",
                    processed_files=drawing_list
                )
            except KeyError:
                # Minimal format
                return self.prompt["user"].format(
                    param_context=param_context,
                    drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                    dxf_text=dxf_text_content
                )
    
    def _parse_and_process_response(self, content: str, parameters_df, 
                                  valid_images: List[str], dxf_files: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Parse AI response and create final result."""
        # Try intelligent parsing first
        success, intelligent_result = self.data_processor.parse_csv_from_response(content)
        
        if success:
            comparisons_df = self.data_processor.standardize_columns_intelligently(intelligent_result)
            metrics = self.data_processor.get_compliance_metrics(comparisons_df)
            
            return True, {
                "comparisons_df": comparisons_df,
                "comparisons_csv": comparisons_df.to_csv(index=False),
                "compliance_metrics": metrics,
                "method": f"Intelligent AI Analysis ({self.provider})",
                "info": f"Analyzed {len(valid_images)} images and {len(dxf_files)} DXF files"
            }
        else:
            return False, {"error": "Failed to parse AI response"}
    
    # ==== CONVENIENCE METHODS ====
    
    def process_drawing_files(self, drawing_files: List, parameters_file_path: str, 
                            api_key: str, upload_dir: str = "uploads") -> Dict[str, Any]:
        """Complete processing: save files, analyze, and prepare results."""
        result = {
            'file_summary': self.get_file_summary(drawing_files),
            'analysis_success': False,
            'analysis_result': None,
            'compliance_metrics': None,
            'error': None
        }
        
        try:
            # Save files
            image_paths = self.save_uploaded_files(drawing_files, upload_dir)
            
            # Analyze
            success, analysis_result = self.analyze_drawings(image_paths, parameters_file_path, api_key)
            result['analysis_success'] = success
            
            if success:
                result['analysis_result'] = analysis_result
                if 'comparisons_df' in analysis_result:
                    result['compliance_metrics'] = self.data_processor.get_compliance_metrics(
                        analysis_result['comparisons_df']
                    )
            else:
                result['error'] = analysis_result.get('error')
                
        except Exception as exception:
            result['error'] = f"Processing error: {str(exception)}"
        
        return result
    
    def get_compliance_metrics(self, comparisons_df) -> Dict[str, Any]:
        """Calculate compliance metrics from comparison DataFrame."""
        return self.data_processor.get_compliance_metrics(comparisons_df)