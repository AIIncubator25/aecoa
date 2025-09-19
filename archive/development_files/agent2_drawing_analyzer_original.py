"""
Agent 2: Drawing Analysis Agent
Analyzes JPG/DXF drawings to extract parameter values and determine compliance status.
"""
import os
import pandas as pd
import requests
import json
import base64
import re
import yaml
from pathlib import Path
from typing import Tuple, Dict, Any, List
from ..utils.prompt_manager import load_agent_prompts

# Try to import ezdxf for DXF text extraction
try:
    import ezdxf
    DXF_AVAILABLE = True
except ImportError:
    DXF_AVAILABLE = False
    print("[WARNING] ezdxf not available - DXF text extraction disabled")

# Agent 2 now uses prompts from external files managed by PromptManager

class DrawingAnalysisAgent:
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        # Load prompts from files instead of hardcoded
        self.prompt = load_agent_prompts("agent2")
        # Initialize compliance template system
        self.compliance_templates = self._load_compliance_templates()
        self.current_domain = 'hs_household_shelter'  # Default domain
        
        # Load HS scenario configurations for scalability
        self.hs_scenarios = self._load_hs_scenarios()
        self.current_scenario = None  # Will be set based on analysis context
        
    def _load_compliance_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load compliance-specific templates for different analysis types.
        This allows the system to be configured for different compliance domains.
        """
        templates = {
            'hs_household_shelter': {
                'name': 'Household Shelter (HS) Analysis',
                'key_columns': [
                    'No', 'Clause', 'Parameter', 'Min_Rectilinear_Area', 'Min_Irregular_Area', 
                    'Unit', 'Min_Volume', 'Unit_Area', 'HS_Area', 'HS_Volume', 
                    'HS_Slab_Thickness', 'HS_Staircase_Thickness', 'Compliance_Status', 
                    'Reference_Drawing', 'Notes'
                ],
                'domain_patterns': {
                    'HS_Area': ['hs area', 'household shelter area', 'shelter area'],
                    'HS_Volume': ['hs volume', 'household shelter volume', 'shelter volume'],
                    'HS_Slab_Thickness': ['hs slab thickness', 'ceiling thickness', 'slab thickness'],
                    'HS_Staircase_Thickness': ['waist thickness', 'staircase thickness', 'stair waist']
                }
            },
            'fire_safety': {
                'name': 'Fire Safety Analysis',
                'key_columns': [
                    'No', 'Clause', 'Parameter', 'Required_Value', 'Found_Value', 
                    'Unit', 'Fire_Rating', 'Egress_Width', 'Travel_Distance', 
                    'Compliance_Status', 'Reference_Drawing', 'Notes'
                ],
                'domain_patterns': {
                    'Fire_Rating': ['fire rating', 'fire resistance', 'fire duration'],
                    'Egress_Width': ['egress width', 'exit width', 'corridor width'],
                    'Travel_Distance': ['travel distance', 'egress distance', 'exit distance']
                }
            },
            'accessibility': {
                'name': 'Accessibility Analysis',
                'key_columns': [
                    'No', 'Clause', 'Parameter', 'Required_Value', 'Found_Value', 
                    'Unit', 'Ramp_Gradient', 'Door_Width', 'Clear_Height', 
                    'Compliance_Status', 'Reference_Drawing', 'Notes'
                ],
                'domain_patterns': {
                    'Ramp_Gradient': ['ramp gradient', 'slope', 'accessibility slope'],
                    'Door_Width': ['door width', 'opening width', 'accessible width'],
                    'Clear_Height': ['clear height', 'headroom', 'clearance height']
                }
            },
            'structural': {
                'name': 'Structural Analysis',
                'key_columns': [
                    'No', 'Clause', 'Parameter', 'Required_Value', 'Found_Value', 
                    'Unit', 'Load_Capacity', 'Thickness', 'Reinforcement', 
                    'Compliance_Status', 'Reference_Drawing', 'Notes'
                ],
                'domain_patterns': {
                    'Load_Capacity': ['load capacity', 'structural capacity', 'bearing capacity'],
                    'Thickness': ['thickness', 'slab thickness', 'wall thickness'],
                    'Reinforcement': ['reinforcement', 'rebar', 'steel reinforcement']
                }
            }
            }
        
        return templates
    
    def _load_hs_scenarios(self) -> Dict[str, Any]:
        """Load HS scenario configurations for different project types."""
        try:
            # Get project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            scenarios_path = os.path.join(project_root, 'configurations', 'hs_scenarios.yaml')
            
            if os.path.exists(scenarios_path):
                with open(scenarios_path, 'r', encoding='utf-8') as f:
                    scenarios_data = yaml.safe_load(f)
                print(f"[DEBUG] Loaded {len(scenarios_data.get('scenarios', {}))} HS scenarios")
                return scenarios_data
            else:
                print(f"[WARNING] HS scenarios file not found: {scenarios_path}")
                return {'scenarios': {}, 'default_scenario': 'residential_standard'}
        except Exception as e:
            print(f"[ERROR] Failed to load HS scenarios: {e}")
            return {'scenarios': {}, 'default_scenario': 'residential_standard'}
    
    def set_hs_scenario(self, scenario_name: str):
        """Set the HS scenario for analysis (e.g., 'residential_standard', 'hdb_standard')."""
        scenarios = self.hs_scenarios.get('scenarios', {})
        if scenario_name in scenarios:
            self.current_scenario = scenario_name
            print(f"[DEBUG] Set HS scenario to: {scenarios[scenario_name]['name']}")
        else:
            available_scenarios = list(scenarios.keys())
            default_scenario = self.hs_scenarios.get('default_scenario', 'residential_standard')
            print(f"[WARNING] Unknown scenario '{scenario_name}'. Available: {available_scenarios}")
            self.current_scenario = default_scenario
    
    def set_compliance_domain(self, domain: str):
        """
        Set the compliance domain for analysis (e.g., 'hs_household_shelter', 'fire_safety').
        This configures the system for domain-specific column patterns and templates.
        """
        if domain in self.compliance_templates:
            self.current_domain = domain
            print(f"[DEBUG] Set compliance domain to: {self.compliance_templates[domain]['name']}")
        else:
            available_domains = list(self.compliance_templates.keys())
            print(f"[WARNING] Unknown domain '{domain}'. Available domains: {available_domains}")
            self.current_domain = 'hs_household_shelter'  # Default fallback
        
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent (compatibility with app.py)."""
        return load_agent_prompts("agent2")
        
    def set_intelligent_mode(self, use_intelligent: bool = True):
        """Switch to intelligent AI-focused analysis mode."""
        if use_intelligent:
            # Load the intelligent prompts - Use HS-specific prompts if available
            try:
                import os
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                
                # Try HS-specific prompts first
                hs_system_path = os.path.join(project_root, 'prompts', 'agent2_hs_system.txt')
                hs_user_path = os.path.join(project_root, 'prompts', 'agent2_hs_user.txt')
                
                if os.path.exists(hs_system_path) and os.path.exists(hs_user_path):
                    with open(hs_system_path, 'r', encoding='utf-8') as f:
                        system_prompt = f.read()
                    with open(hs_user_path, 'r', encoding='utf-8') as f:
                        user_prompt = f.read()
                    print("[DEBUG] Using HS-specific intelligent prompts")
                else:
                    # Fallback to generic intelligent prompts
                    system_path = os.path.join(project_root, 'prompts', 'agent2_intelligent_system.txt')
                    user_path = os.path.join(project_root, 'prompts', 'agent2_intelligent_user.txt')
                    
                    with open(system_path, 'r', encoding='utf-8') as f:
                        system_prompt = f.read()
                    with open(user_path, 'r', encoding='utf-8') as f:
                        user_prompt = f.read()
                    print("[DEBUG] Using generic intelligent prompts")
                
                self.prompt = {
                    "system": system_prompt,
                    "user": user_prompt
                }
                print("[DEBUG] Switched to intelligent AI-focused mode")
            except Exception as e:
                print(f"[WARNING] Could not load intelligent prompts: {e}")
                print("[DEBUG] Continuing with default prompts")
        else:
            # Revert to default prompts
            self.prompt = load_agent_prompts("agent2")
            
    def _standardize_columns_intelligently(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Intelligently standardize column names using domain-specific templates.
        Uses semantic understanding and compliance domain patterns for accurate mapping.
        """
        standardized_df = df.copy()
        
        # Get domain-specific patterns if available
        domain_patterns = {}
        if hasattr(self, 'current_domain') and self.current_domain in self.compliance_templates:
            domain_patterns = self.compliance_templates[self.current_domain].get('domain_patterns', {})
            print(f"[DEBUG] Using domain-specific patterns for {self.current_domain}")
        
        # Combine universal patterns with domain-specific patterns
        universal_patterns = {
            # Universal identification columns
            'No': ['no', 'number', 'item', '#', 'id', 'index', 'seq'],
            'Clause': ['clause', 'section', 'requirement', 'code', 'regulation'],
            'Parameter': ['parameter', 'requirement', 'criteria', 'item', 'specification'],
            
            # Universal result columns
            'Unit': ['unit', 'units', 'measurement unit', 'uom', 'measure'],
            'Unit_Area': ['unit area', 'area unit', 'unit_area', 'area measurement unit'],
            'Found_Value': ['found value', 'actual value', 'measured value', 'identified value'],
            'Required_Value': ['required value', 'minimum value', 'standard value', 'target value'],
            'Compliance_Status': ['compliance', 'status', 'result', 'compliant', 'pass/fail'],
            'Reference_Drawing': ['reference', 'drawing', 'source', 'ref', 'plan reference'],
            'Notes': ['notes', 'remarks', 'comments', 'observations', 'analysis'],
            'Method': ['method', 'approach', 'technique', 'detection method']
        }
        
        # Merge domain-specific patterns with universal ones
        all_patterns = {**universal_patterns, **domain_patterns}
        
        # Create mapping based on semantic similarity
        column_mapping = {}
        for col in standardized_df.columns:
            col_lower = col.lower().strip()
            
            # Find best match using multiple criteria
            best_match = None
            max_score = 0
            
            for standard_name, patterns in all_patterns.items():
                for pattern in patterns:
                    # Calculate similarity score with better prioritization
                    pattern_lower = pattern.lower()
                    col_clean = col_lower.replace(' ', '').replace('_', '')
                    pattern_clean = pattern_lower.replace(' ', '').replace('_', '')
                    
                    if pattern_lower == col_lower:
                        score = 1.0  # Perfect match
                    elif pattern_clean == col_clean:
                        score = 0.95  # Perfect match ignoring spaces/underscores
                    elif pattern_lower in col_lower:
                        # Longer patterns get higher scores
                        score = 0.8 + (len(pattern_lower) / len(col_lower)) * 0.1
                    elif col_lower in pattern_lower:
                        score = 0.6 + (len(col_lower) / len(pattern_lower)) * 0.1
                    elif self._fuzzy_match(pattern_lower, col_lower):
                        score = 0.5
                    else:
                        score = 0
                    
                    if score > max_score:
                        max_score = score
                        best_match = standard_name
            
            if best_match and max_score > 0.4:  # Threshold for similarity
                column_mapping[col] = best_match
            else:
                # Keep original name but clean it for consistency
                clean_name = self._clean_column_name(col)
                column_mapping[col] = clean_name
        
        # Apply the mapping
        standardized_df = standardized_df.rename(columns=column_mapping)
        
        print(f"[DEBUG] Domain-aware column mapping applied: {column_mapping}")
        
        return standardized_df
    
    def _clean_json_intelligently(self, json_content: str) -> str:
        """
        Intelligently clean JSON content using pattern recognition rather than hardcoded fixes.
        This method is agnostic to specific parameter names and compliance types.
        """
        # Generic JSON formatting fixes (not parameter-specific)
        patterns = [
            # Fix newlines within quoted strings
            (r'"\s*\n\s*([^"]*)"', r'"\1"'),
            # Fix newlines between quotes
            (r'"\s*\n\s*"', r'""'),
            # Fix comma-newline combinations
            (r'",\s*\n\s*"', r'", "'),
            # Fix trailing whitespace in quoted strings
            (r'"\s*([^"]*?)\s*"', r'"\1"'),
            # Fix multiple spaces within strings
            (r'"([^"]*?)\s{2,}([^"]*?)"', r'"\1 \2"'),
        ]
        
        cleaned = json_content
        for pattern, replacement in patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned

    def _fuzzy_match(self, pattern: str, column: str) -> bool:
        """Simple fuzzy matching for column names."""
        # Check for common variations and abbreviations
        pattern_words = set(pattern.replace('_', ' ').split())
        column_words = set(column.replace('_', ' ').split())
        
        # Calculate word overlap
        overlap = len(pattern_words.intersection(column_words))
        total_words = len(pattern_words.union(column_words))
        
        return (overlap / total_words) > 0.5 if total_words > 0 else False
    
    def _clean_column_name(self, column: str) -> str:
        """Clean column name for consistency."""
        # Remove special characters and normalize spacing
        clean_name = column.replace('.', '').replace('(', '').replace(')', '')
        clean_name = clean_name.replace('  ', ' ').strip()
        # Convert to title case with underscores
        clean_name = clean_name.title().replace(' ', '_')
        return clean_name

    def set_prompts(self, prompts: Dict[str, str]):
        """Set custom prompts for the agent."""
        if "user" in prompts:
            default_prompts = load_agent_prompts("agent2")
            self.prompt = {"system": prompts.get("system", default_prompts["system"]),
                          "user": prompts["user"]}
        else:
            self.prompt = prompts
    
    def get_file_summary(self, drawing_files: List) -> Dict[str, Any]:
        """Get summary information about uploaded drawing files."""
        jpg_png_count = len([f for f in drawing_files if f.name.lower().endswith(('.jpg', '.jpeg', '.png'))])
        dxf_count = len([f for f in drawing_files if f.name.lower().endswith('.dxf')])
        
        return {
            'total_files': len(drawing_files),
            'image_files': jpg_png_count,
            'dxf_files': dxf_count,
            'file_names': [f.name for f in drawing_files]
        }
    
    def save_uploaded_files(self, drawing_files: List, upload_dir: str = "uploads") -> List[str]:
        """Save uploaded files to local directory and return file paths."""
        import os
        os.makedirs(upload_dir, exist_ok=True)
        image_paths = []
        
        for file in drawing_files:
            file_path = os.path.join(upload_dir, file.name)
            with open(file_path, "wb") as f:
                f.write(file.getvalue())
            image_paths.append(file_path)
        
        return image_paths
    
    def extract_dxf_text(self, dxf_file_path: str) -> str:
        """Extract text content from DXF files using ezdxf."""
        if not DXF_AVAILABLE:
            return "DXF text extraction not available (ezdxf not installed)"
        
        try:
            # Read DXF file
            doc = ezdxf.readfile(dxf_file_path)
            extracted_text = []
            
            # Extract text from all layouts (model space and paper space)
            for layout in doc.layouts:
                layout_name = layout.name
                extracted_text.append(f"=== LAYOUT: {layout_name} ===")
                
                # Extract TEXT entities
                for entity in layout.query('TEXT'):
                    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                        text_content = entity.dxf.text.strip()
                        if text_content:
                            # Include layer and text height for context
                            layer = getattr(entity.dxf, 'layer', 'UNKNOWN') 
                            height = getattr(entity.dxf, 'height', 0)
                            extracted_text.append(f"TEXT[{layer}|H:{height:.1f}]: {text_content}")
                
                # Extract MTEXT entities (multi-line text)
                for entity in layout.query('MTEXT'):
                    if hasattr(entity, 'text'):
                        text_content = entity.text.strip()
                        if text_content:
                            # Clean up MTEXT formatting codes
                            cleaned_text = re.sub(r'\\[A-Za-z][0-9]*;?', '', text_content)
                            cleaned_text = re.sub(r'\{[^}]*\}', '', cleaned_text)
                            if cleaned_text.strip():
                                layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                                extracted_text.append(f"MTEXT[{layer}]: {cleaned_text.strip()}")
                
                # Extract DIMENSION entities (dimension text)
                for entity in layout.query('DIMENSION'):
                    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                        text_content = entity.dxf.text.strip()
                        if text_content:
                            layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                            extracted_text.append(f"DIM[{layer}]: {text_content}")
                
                # Extract LEADER entities (callout text)
                for entity in layout.query('LEADER'):
                    if hasattr(entity, 'dxf'):
                        # Leaders often have associated text entities
                        layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                        extracted_text.append(f"LEADER[{layer}]: Found callout")
                
                # Extract ATTRIB entities (attributes in blocks)
                for entity in layout.query('ATTRIB'):
                    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'text'):
                        text_content = entity.dxf.text.strip()
                        if text_content:
                            tag = getattr(entity.dxf, 'tag', 'UNKNOWN')
                            layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                            extracted_text.append(f"ATTRIB[{tag}|{layer}]: {text_content}")
                
                # Extract INSERT entities with attributes (blocks with text)
                for entity in layout.query('INSERT'):
                    if entity.has_attrib:
                        block_name = entity.dxf.name
                        layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                        extracted_text.append(f"BLOCK[{layer}]: {block_name}")
                        for attrib in entity.attribs:
                            if hasattr(attrib, 'dxf') and hasattr(attrib.dxf, 'text'):
                                text_content = attrib.dxf.text.strip()
                                tag = getattr(attrib.dxf, 'tag', 'UNKNOWN')
                                if text_content:
                                    extracted_text.append(f"  {tag}: {text_content}")
                
                # Extract TABLE entities (basic table data if available)
                try:
                    for entity in layout.query('ACAD_TABLE'):
                        if hasattr(entity, 'text'):
                            layer = getattr(entity.dxf, 'layer', 'UNKNOWN')
                            extracted_text.append(f"TABLE[{layer}]: Table data found")
                except:
                    pass  # ACAD_TABLE might not be available in all DXF versions
                
                extracted_text.append("")  # Add blank line between layouts
            
            result = "\n".join(extracted_text)
            
            if result.strip():
                print(f"[DEBUG] Extracted {len(extracted_text)} text elements from {os.path.basename(dxf_file_path)}")
                return result
            else:
                return f"No text content found in DXF file: {os.path.basename(dxf_file_path)}"
                
        except Exception as e:
            error_msg = f"Error extracting text from DXF {os.path.basename(dxf_file_path)}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return error_msg
    
    def get_compliance_metrics(self, comparisons_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate compliance metrics from comparison DataFrame."""
        total = len(comparisons_df)
        compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
        non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
        not_found = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Not Found'])
        
        return {
            'total_parameters': total,
            'compliant': compliant,
            'non_compliant': non_compliant,
            'not_found': not_found,
            'compliance_rate': (compliant / total * 100) if total > 0 else 0,
            'non_compliance_rate': (non_compliant / total * 100) if total > 0 else 0,
            'not_found_rate': (not_found / total * 100) if total > 0 else 0
        }
    
    def process_drawing_files(self, drawing_files: List, parameters_file_path: str, api_key: str, upload_dir: str = "uploads") -> Dict[str, Any]:
        """Complete Step 2 processing: save files, analyze, and prepare results."""
        result = {
            'file_summary': self.get_file_summary(drawing_files),
            'analysis_success': False,
            'analysis_result': None,
            'compliance_metrics': None,
            'error': None
        }
        
        try:
            # Save uploaded files
            image_paths = self.save_uploaded_files(drawing_files, upload_dir)
            
            # Analyze drawings
            success, analysis_result = self.analyze_drawings(image_paths, parameters_file_path, api_key)
            result['analysis_success'] = success
            
            if success:
                result['analysis_result'] = analysis_result
                # Calculate compliance metrics
                if 'comparisons_df' in analysis_result:
                    result['compliance_metrics'] = self.get_compliance_metrics(analysis_result['comparisons_df'])
            else:
                result['error'] = analysis_result.get('error')
                
        except Exception as e:
            result['error'] = f"Processing error: {str(e)}"
        
        return result
    
    def analyze_drawings(self, image_paths: List[str], parameters_file_path: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Analyze drawings against parameters using AI prompt-response approach.
        
        Args:
            image_paths: List of paths to JPG/PNG files 
            parameters_file_path: Path to parameters file (CSV or JSON from Step 1)
            api_key: Required API key for AI provider
            
        Returns:
            Tuple[bool, Dict]: (success, {"comparisons_df": DataFrame, "comparisons_csv": str})
        """
        if not api_key:
            return False, {"error": "API key is required for AI prompt-response approach"}
            
        try:
            # Load parameters from CSV or JSON
            if not os.path.exists(parameters_file_path):
                return False, {"error": f"Parameters file not found: {parameters_file_path}"}
            
            # Check if it's JSON or CSV
            if parameters_file_path.endswith('.json'):
                parameters_df = self._load_parameters_from_json(parameters_file_path)
            else:
                parameters_df = pd.read_csv(parameters_file_path)
            
            # Filter to JPG/PNG only
            valid_images = [p for p in image_paths if p.lower().endswith(('.jpg', '.jpeg', '.png'))]
            dxf_files = [p for p in image_paths if p.lower().endswith('.dxf')]
            
            if not valid_images:
                return False, {"error": "No valid image files (JPG/PNG) provided for analysis"}
            
            return self._analyze_with_ai(parameters_df, valid_images, dxf_files, api_key)
            
        except Exception as e:
            return False, {"error": f"Drawing analysis failed: {str(e)}"}
    
    def _load_parameters_from_json(self, json_path: str) -> pd.DataFrame:
        """Convert JSON parameters to DataFrame format compatible with CSV structure."""
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Extract parameters from JSON structure
        parameters = []
        
        # Get parameter templates from JSON
        param_templates = json_data.get('parameters', {}).get('parameter_templates', {})
        
        for param_name, param_info in param_templates.items():
            # Use the parameter info as-is from the JSON, don't add artificial columns
            param_dict = {
                'parameter': param_name,
                'description': param_info.get('description', ''),
                'value': param_info.get('value', ''),
                'unit': param_info.get('unit', ''),
                'type': param_info.get('type', ''),
                'source': param_info.get('source', '')
            }
            
            # Add any additional fields that exist in the JSON naturally
            for key, value in param_info.items():
                if key not in param_dict:
                    param_dict[key] = value
                    
            parameters.append(param_dict)
        
        return pd.DataFrame(parameters)
    
    def _analyze_with_ai(self, parameters_df: pd.DataFrame, image_paths: List[str], dxf_files: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Analyze drawings using enhanced AI prompts with provider support."""
        
        # Store for debugging purposes
        self.current_dxf_files = dxf_files
        
        try:
            # Prepare context from parameters
            param_rows = []
            for _, row in parameters_df.iterrows():
                param_rows.append(f"{row['parameter']}: {row['description']} (required: {row['value']} {row['unit']})")
            param_context = "\n".join(param_rows)
            
            # Prepare drawing list
            drawing_list = [Path(p).name for p in image_paths]
            
            # Extract text from DXF files
            dxf_text_content = []
            for dxf_file in dxf_files:
                dxf_text = self.extract_dxf_text(dxf_file)
                if dxf_text and not dxf_text.startswith("Error") and not dxf_text.startswith("No text content"):
                    dxf_text_content.append(f"=== DXF FILE: {os.path.basename(dxf_file)} ===")
                    dxf_text_content.append(dxf_text)
                    dxf_text_content.append("")
            
            dxf_text_combined = "\n".join(dxf_text_content) if dxf_text_content else "No DXF text content available"
            
            # Format user prompt with context - handle different prompt templates
            try:
                # First try with HS-specific placeholders
                user_prompt = self.prompt["user"].format(
                    param_context=param_context,
                    drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                    dxf_content=dxf_text_combined,  # Use dxf_content to match HS prompt template
                )
                print(f"[DEBUG] Formatted prompt with HS-specific placeholders")
            except KeyError as e:
                print(f"[DEBUG] Missing placeholder {e}, trying generic format...")
                # For generic prompts that use different placeholders
                try:
                    user_prompt = self.prompt["user"].format(
                        param_context=param_context,
                        drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                        hints="",  # Optional hints - empty for now
                        dxf_text=dxf_text_combined,  # Generic format uses dxf_text
                        processed_files=drawing_list
                    )
                    print(f"[DEBUG] Formatted prompt with generic placeholders")
                except KeyError as e2:
                    print(f"[DEBUG] Missing placeholder {e2}, trying minimal format...")
                    # For minimal prompts
                    user_prompt = self.prompt["user"].format(
                        param_context=param_context,
                        drawing_list="\n".join([f"- {name}" for name in drawing_list]),
                        dxf_text=dxf_text_combined  # Minimal format
                    )

            # Call appropriate provider
            if self.provider == "OpenAI":
                success, result = self._call_openai(user_prompt, image_paths, api_key)
            elif self.provider == "GovTech":
                success, result = self._call_govtech(user_prompt, image_paths, api_key)
            else:
                return False, {"error": f"Unsupported provider: {self.provider}. Drawing analysis requires OpenAI or GovTech."}
            
            if not success:
                return False, result
                
            content = result.get('content', '')
            
            # Try intelligent AI-focused parsing first
            print("[DEBUG] Attempting intelligent AI-focused parsing...")
            success, intelligent_result = self._parse_ai_response_intelligent(content, parameters_df)
            
            if success:
                print("[DEBUG] Intelligent parsing successful!")
                return success, intelligent_result
            else:
                print(f"[DEBUG] Intelligent parsing failed: {intelligent_result.get('error')}")
                print("[DEBUG] Falling back to JSON parsing...")
                # Fallback to original JSON parsing method (pass dxf_files from this scope)
                return self._parse_ai_response(content, parameters_df, image_paths, dxf_files)
                
        except requests.exceptions.RequestException as req_err:
            return False, {"error": f"API request failed: {str(req_err)}"}
        except Exception as general_err:
            return False, {"error": f"AI analysis failed: {str(general_err)}"}
    
    def _call_openai(self, user_prompt: str, image_paths: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Call OpenAI API for drawing analysis."""
        try:
            # Encode images with proper MIME type detection
            images_data = []
            for img_path in image_paths:
                try:
                    # Determine MIME type based on file extension
                    ext = os.path.splitext(img_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        mime_type = "image/jpeg"
                    elif ext == '.png':
                        mime_type = "image/png"
                    else:
                        print(f"[WARNING] Unknown image type for {img_path}, using jpeg")
                        mime_type = "image/jpeg"
                    
                    with open(img_path, 'rb') as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        images_data.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{img_data}"}
                        })
                        print(f"[DEBUG] Successfully encoded {os.path.basename(img_path)} as {mime_type}")
                except Exception as e:
                    print(f"[ERROR] Failed to encode {os.path.basename(img_path)}: {e}")
                    continue
            
            if not images_data:
                return False, {"error": "Failed to encode any images"}
            
            print(f"[DEBUG] Successfully encoded {len(images_data)} images for OpenAI analysis")
            
            # Save debug information
            debug_info = {
                "timestamp": str(pd.Timestamp.now()),
                "provider": self.provider,
                "model": self.model,
                "image_count": len(images_data),
                "dxf_count": len(getattr(self, 'current_dxf_files', [])),
                "system_prompt_length": len(self.prompt["system"]),
                "user_prompt_length": len(user_prompt)
            }
            
            # Save prompts for debugging
            try:
                with open("debug_agent2_prompts.txt", "w", encoding='utf-8') as f:
                    f.write("=== AGENT 2 DEBUG INFO ===\n")
                    f.write(f"Timestamp: {debug_info['timestamp']}\n")
                    f.write(f"Provider: {debug_info['provider']}\n")
                    f.write(f"Model: {debug_info['model']}\n")
                    f.write(f"Images: {debug_info['image_count']}\n")
                    f.write(f"DXF files: {debug_info['dxf_count']}\n")
                    f.write(f"System prompt length: {debug_info['system_prompt_length']}\n")
                    f.write(f"User prompt length: {debug_info['user_prompt_length']}\n\n")
                    f.write("=== SYSTEM PROMPT ===\n")
                    f.write(self.prompt["system"])
                    f.write("\n\n=== USER PROMPT ===\n")
                    f.write(user_prompt)
                print("[DEBUG] Saved debug prompts to debug_agent2_prompts.txt")
            except Exception as e:
                print(f"[WARNING] Could not save debug prompts: {e}")
            
            # Build messages
            messages = [
                {"role": "system", "content": self.prompt["system"]},
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": user_prompt}] + images_data
                }
            ]
            
            # Make OpenAI API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"].strip()
            return True, {"content": content}
            
        except Exception as e:
            return False, {"error": f"OpenAI API call failed: {str(e)}"}
    
    def _call_govtech(self, user_prompt: str, image_paths: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Call GovTech API for drawing analysis."""
        # Note: This is a placeholder - GovTech API may not support image analysis
        return False, {"error": "GovTech API does not currently support image analysis. Please use OpenAI provider."}
    
    def _parse_ai_response(self, content: str, parameters_df: pd.DataFrame, image_paths: List[str], dxf_files: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """Parse AI response and build comparison DataFrame."""
        try:
            # Enhanced cleaning of AI response
            original_content = content
            
            # Remove markdown markers
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            # Remove common AI response prefixes
            content = content.strip()
            if content.startswith("Here is the analysis:"):
                content = content.replace("Here is the analysis:", "").strip()
            if content.startswith("Here's the analysis:"):
                content = content.replace("Here's the analysis:", "").strip()
            
            # Clean up whitespace and newline issues in JSON keys/values
            import re
            # Fix newlines at the start of JSON keys
            content = re.sub(r'"\s*\n\s*"([^"]+)"', r'"\1"', content)
            # Fix newlines within JSON strings
            content = re.sub(r':\s*"\s*\n\s*([^"]*)"', r': "\1"', content)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            
            # Try to find JSON boundaries if response contains extra text
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                content = content[json_start:json_end+1]
            
            try:
                data = json.loads(content)
                print("[DEBUG] JSON parsing successful!")
            except json.JSONDecodeError as json_err:
                # Enhanced debugging for JSON parsing failures
                print(f"[DEBUG] JSON parsing failed: {json_err}")
                print(f"[DEBUG] Error at position {json_err.pos}")
                print(f"[DEBUG] Problematic content (first 500 chars): {content[:500]}")
                print(f"[DEBUG] Original content (first 500 chars): {original_content[:500]}")
                
                if json_err.pos < len(content):
                    error_context = content[max(0, json_err.pos-50):json_err.pos+50]
                    print(f"[DEBUG] Error context: ...{error_context}...")
                
                # Try more aggressive cleaning approaches using intelligent patterns
                cleaned_content = re.sub(r'\s+', ' ', content.strip())
                
                # Apply intelligent JSON cleaning patterns (agnostic to specific parameters)
                cleaned_content = self._clean_json_intelligently(cleaned_content)
                
                try:
                    data = json.loads(cleaned_content)
                    print("[DEBUG] JSON parsing successful after aggressive cleaning!")
                except json.JSONDecodeError as final_err:
                    print(f"[DEBUG] Final JSON parsing attempt failed: {final_err}")
                    # Save problematic content to file for inspection
                    with open("debug_json_error.txt", "w", encoding='utf-8') as f:
                        f.write(f"Original content:\n{original_content}\n\n")
                        f.write(f"Cleaned content:\n{cleaned_content}\n\n")
                        f.write(f"Error: {final_err}\n")
                    raise final_err
            
            # Extract comparison data from AI response
            compliance_analysis = data.get("compliance_analysis", [])
            comparisons_csv = data.get("comparisons_csv", "")
            drawing_titles = data.get("drawing_titles", [])
            
            # Build DataFrame from compliance analysis
            comparisons_data = []
            
            # Match AI results to parameters structure  
            for _, param_row in parameters_df.iterrows():
                param_name = param_row['parameter']
                
                # Find AI analysis for this parameter
                ai_result = None
                for analysis in compliance_analysis:
                    if analysis.get('parameter') == param_name:
                        ai_result = analysis
                        break
                
                if ai_result:
                    comparisons_data.append({
                        "Parameter": param_name,
                        "Required_Value": ai_result.get('required_value', param_row.get('value', '')),
                        "Unit": ai_result.get('unit', param_row.get('unit', '')),
                        "Found_Value": ai_result.get('found_value', ''),
                        "Compliance_Status": ai_result.get('compliance_status', 'Not Found'),
                        "Source": ai_result.get('source', ''),
                        "Method": ai_result.get('method', 'ocr'),
                        "Confidence": ai_result.get('confidence', 0.0),
                        "Notes": ai_result.get('notes', ''),
                        "Description": param_row.get('description', '')
                    })
                else:
                    # Parameter not found in AI analysis
                    comparisons_data.append({
                        "Parameter": param_name,
                        "Required_Value": param_row.get('value', ''),
                        "Unit": param_row.get('unit', ''),
                        "Found_Value": "",
                        "Compliance_Status": "Not Found",
                        "Source": "",
                        "Method": "ai",
                        "Confidence": 0.0,
                        "Notes": "Not detected in drawings",
                        "Description": param_row.get('description', '')
                    })
            
            comparisons_df = pd.DataFrame(comparisons_data)
            
            # Save to CSV
            csv_path = "comparisons.csv"
            comparisons_df.to_csv(csv_path, index=False)
            
            result_info = f"AI analyzed {len(image_paths)} image files"
            if dxf_files:
                result_info += f" and extracted text from {len(dxf_files)} DXF files"
            
            return True, {
                "comparisons_df": comparisons_df,
                "comparisons_csv": csv_path,
                "ai_csv_data": comparisons_csv,
                "drawing_titles": drawing_titles,
                "method": f"Enhanced AI Analysis ({self.provider})", 
                "info": result_info
            }
            
        except json.JSONDecodeError as json_err:
            # Enhanced error reporting for JSON parsing issues
            error_msg = f"Failed to parse AI response as JSON: {str(json_err)}"
            print(f"JSON Error Details: {json_err}")
            print(f"Content that failed to parse: {content}")
            if len(original_content) < 1000:
                error_msg += f"\nFull AI response: '{original_content}'"
            else:
                error_msg += f"\nAI response preview: '{original_content[:500]}...'"
            return False, {"error": error_msg}
            
    def _parse_ai_response_intelligent(self, content: str, parameters_df: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        AI-focused parsing approach that leverages AI's intelligence rather than rigid JSON parsing.
        This method supports both simple CSV format and detailed comparison format.
        """
        try:
            print(f"[DEBUG] AI Response length: {len(content)}")
            print(f"[DEBUG] First 300 chars: {content[:300]}")
            
            # Clean up the response to find CSV content
            lines = content.split('\n')
            csv_lines = []
            in_csv = False
            
            print(f"[DEBUG] Total lines in response: {len(lines)}")
            print(f"[DEBUG] First 5 lines: {lines[:5]}")
            
            for line in lines:
                line = line.strip()
                # More flexible CSV header detection
                if any(header in line.lower() for header in [
                    'parameter,', 'no,clause,', 'no,parameter', 'clause,parameter',
                    # Also look for the specific format requested in prompts
                    'min. rectilinear', 'min. irregular', 'unit area', 'hs area'
                ]):
                    in_csv = True
                    csv_lines.append(line)
                    print(f"[DEBUG] Found CSV header: {line}")
                elif in_csv and (',' in line and len(line.split(',')) >= 4):
                    csv_lines.append(line)
                elif in_csv and line == '':
                    continue  # Allow empty lines in CSV
                elif in_csv and not line:
                    break  # End of CSV block
            
            # More aggressive fallback detection
            if not csv_lines:
                print("[DEBUG] No header match, trying fallback detection...")
                # Look for any substantial CSV-like content
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.count(',') >= 8 and len(line) > 50:  # Looks like a substantial CSV line
                        csv_lines.append(line)
                        print(f"[DEBUG] Found CSV-like line {i}: {line[:100]}...")
                        # Look for preceding header line
                        if i > 0:
                            prev_line = lines[i-1].strip()
                            if prev_line.count(',') >= 8:
                                csv_lines.insert(0, prev_line)
                                print(f"[DEBUG] Added header line: {prev_line[:100]}...")
                                break
            
            # Final fallback - look for any lines with many commas
            if not csv_lines:
                print("[DEBUG] Trying final fallback - looking for comma-rich lines...")
                comma_lines = []
                for i, line in enumerate(lines):
                    if line.count(',') >= 5:
                        comma_lines.append((i, line.strip(), line.count(',')))
                
                if comma_lines:
                    # Sort by comma count and take the top ones
                    comma_lines.sort(key=lambda x: x[2], reverse=True)
                    print(f"[DEBUG] Found {len(comma_lines)} comma-rich lines")
                    for i, (line_num, line_content, comma_count) in enumerate(comma_lines[:5]):
                        print(f"[DEBUG] Line {line_num} ({comma_count} commas): {line_content[:100]}...")
                        csv_lines.append(line_content)
            
            if not csv_lines:
                print("[ERROR] No CSV structure found in AI response")
                print(f"[DEBUG] Full AI response for inspection:")
                print(f"[DEBUG] Response: {content}")
                # Save the problematic response for debugging
                with open("debug_ai_response_no_csv.txt", "w", encoding='utf-8') as f:
                    f.write(f"AI Response (length: {len(content)}):\n")
                    f.write(content)
                print("[DEBUG] Saved response to debug_ai_response_no_csv.txt")
                return False, {"error": "AI did not return data in expected CSV format"}
            
            print(f"[DEBUG] Found {len(csv_lines)} CSV lines")
            
            # Parse CSV data
            import io
            csv_content = '\n'.join(csv_lines)
            print(f"[DEBUG] CSV content: {csv_content[:500]}")
            
            try:
                df = pd.read_csv(io.StringIO(csv_content))
                print(f"[DEBUG] Successfully parsed CSV with {len(df)} rows and {len(df.columns)} columns")
                print(f"[DEBUG] Columns: {list(df.columns)}")
                
                # Determine if this is detailed comparison format or simple format
                is_detailed_format = 'Clause' in df.columns or 'clause' in df.columns
                
                if is_detailed_format:
                    print("[DEBUG] Using detailed comparison format")
                    # Handle detailed comparison format
                    comparison_df = df.copy()
                    
                    # Dynamic column standardization - let AI determine the format
                    comparison_df = self._standardize_columns_intelligently(comparison_df)
                    
                    # Calculate compliance metrics
                    total_params = len(comparison_df)
                    compliant = len(comparison_df[comparison_df.get('Compliance_Status', '').str.contains('Compliant', case=False, na=False)])
                    non_compliant = len(comparison_df[comparison_df.get('Compliance_Status', '').str.contains('Non-Compliant', case=False, na=False)])
                    not_found = total_params - compliant - non_compliant
                    
                    return True, {
                        'comparisons_df': comparison_df,
                        'comparisons_csv': comparison_df.to_csv(index=False),
                        'compliance_summary': {
                            'total': total_params,
                            'compliant': compliant,
                            'non_compliant': non_compliant,
                            'not_found': not_found,
                            'compliance_rate': round((compliant / total_params * 100) if total_params > 0 else 0, 1)
                        },
                        'method': 'Intelligent AI Analysis (Detailed Comparison)',
                        'info': f'Successfully analyzed {total_params} requirements using AI intelligence'
                    }
                    
                else:
                    print("[DEBUG] Using simple CSV format")
                    # Handle simple format (existing logic)
                    column_mapping = {
                        'Parameter': 'Parameter',
                        'parameter': 'Parameter',
                        'Required_Value': 'Required_Value',
                        'required_value': 'Required_Value',
                        'Found_Value': 'Found_Value', 
                        'found_value': 'Found_Value',
                        'Unit': 'Unit',
                        'unit': 'Unit',
                        'Compliance_Status': 'Compliance_Status',
                        'compliance_status': 'Compliance_Status',
                        'Source': 'Source',
                        'source': 'Source',
                        'Method': 'Method',
                        'method': 'Method',
                        'Confidence': 'Confidence',
                        'confidence': 'Confidence',
                        'Notes': 'Notes',
                        'notes': 'Notes'
                    }
                    
                    # Rename columns to standard format
                df = df.rename(columns=column_mapping)
                
                # Ensure required columns exist
                required_columns = ['Parameter', 'Required_Value', 'Found_Value', 'Unit', 'Compliance_Status', 'Source', 'Method', 'Confidence', 'Notes']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # Clean up compliance status
                if 'Compliance_Status' in df.columns:
                    df['Compliance_Status'] = df['Compliance_Status'].str.strip()
                    # Standardize compliance values
                    df['Compliance_Status'] = df['Compliance_Status'].replace({
                        'Y': 'Compliant',
                        'N': 'Non-Compliant',
                        'Compliant': 'Compliant',
                        'Non-Compliant': 'Non-Compliant',
                        'Not Found': 'Not Found',
                        'Not Applicable': 'Not Applicable'
                    })
                
                result_info = f"AI analyzed drawings using intelligent interpretation approach"
                
                return True, {
                    "comparisons_df": df,
                    "method": f"Intelligent AI Analysis ({self.provider})",
                    "info": result_info,
                    "analysis_type": "ai_intelligent"
                }
                
            except Exception as csv_err:
                print(f"[ERROR] CSV parsing failed: {csv_err}")
                print(f"[DEBUG] Raw CSV content: {csv_content}")
                return False, {"error": f"Failed to parse AI response as CSV: {str(csv_err)}"}
            
        except Exception as e:
            print(f"[ERROR] Intelligent parsing failed: {e}")
            return False, {"error": f"AI response parsing error: {str(e)}"}
