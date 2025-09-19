"""
Data Processor for Drawing Analysis
Handles data parsing, standardization, and DataFrame operations.
"""
import io
import json
import re
from typing import Dict, Any, Tuple

import pandas as pd


class DataProcessor:
    """Processes and standardizes data for drawing analysis."""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
    def load_parameters_from_json(self, json_path: str) -> pd.DataFrame:
        """Convert JSON parameters to DataFrame format with 2.10 HS table structure."""
        with open(json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        parameters = []
        
        # Extract metadata for context
        metadata = json_data.get('metadata', {})
        clause_id = metadata.get('clause_id', 'Unknown')
        description = metadata.get('description', '')
        
        # Extract parameter templates
        param_templates = json_data.get('parameters', {}).get('parameter_templates', {})
        
        # Extract tables for requirements mapping
        tables = json_data.get('tables', {})
        min_requirements = tables.get('min_requirements_by_gfa', {}).get('rows', [])
        
        # Create parameters with 2.10 HS table format context
        for param_name, param_info in param_templates.items():
            param_dict = {
                'parameter': param_name,
                'description': param_info.get('description', ''),
                'value': param_info.get('value', ''),
                'unit': param_info.get('unit', ''),
                'type': param_info.get('type', ''),
                'source': param_info.get('source', ''),
                'clause_id': clause_id,
                'full_description': description
            }
            
            # Add table requirements context for GFA-based parameters
            if 'hs_area_clear' in param_name.lower() and min_requirements:
                param_dict['gfa_table'] = min_requirements
                param_dict['table_format_hint'] = ("Use GFA to determine tier: "
                                                  "<40, 40-45, 45-75, 75-140, >140")
            
            # Add any additional fields from JSON
            for key, value in param_info.items():
                if key not in param_dict:
                    param_dict[key] = value
                    
            parameters.append(param_dict)
        
        # Add table information as additional context
        if min_requirements:
            table_context = {
                'parameter': '2.10_HS_GFA_Table_Context',
                'description': 'GFA-based requirements table for HS analysis',
                'value': str(min_requirements),
                'unit': 'table',
                'type': 'context',
                'source': 'Step 1 JSON parameters',
                'clause_id': clause_id,
                'table_format_hint': "This table shows min_area_m2 and min_volume_m3 by GFA ranges"
            }
            parameters.append(table_context)
        
        return pd.DataFrame(parameters)
    
    def standardize_columns_intelligently(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Intelligently standardize column names using domain patterns."""
        standardized_df = dataframe.copy()
        
        # Get domain-specific patterns
        domain_patterns = {}
        if self.config_manager:
            domain_patterns = self.config_manager.get_domain_patterns()
        
        # Universal patterns
        universal_patterns = {
            'No': ['no', 'number', 'item', '#', 'id', 'index', 'seq'],
            'Clause': ['clause', 'section', 'requirement', 'code', 'regulation'],
            'Parameter': ['parameter', 'requirement', 'criteria', 'item', 'specification'],
            'Unit': ['unit', 'units', 'measurement unit', 'uom', 'measure'],
            'Unit_Area': ['unit area', 'area unit', 'unit_area', 'area measurement unit'],
            'Found_Value': ['found value', 'actual value', 'measured value', 'identified value'],
            'Required_Value': ['required value', 'minimum value', 'standard value', 
                              'target value'],
            'Compliance_Status': ['compliance', 'status', 'result', 'compliant', 'pass/fail'],
            'Reference_Drawing': ['reference', 'drawing', 'source', 'ref', 'plan reference'],
            'Notes': ['notes', 'remarks', 'comments', 'observations', 'analysis'],
            'Method': ['method', 'approach', 'technique', 'detection method']
        }
        
        # Merge patterns
        all_patterns = {**universal_patterns, **domain_patterns}
        
        # Create mapping with duplicate prevention
        column_mapping = {}
        used_standard_names = set()
        
        for col in standardized_df.columns:
            best_match = self._find_best_column_match(col, all_patterns)
            
            if best_match and best_match not in used_standard_names:
                column_mapping[col] = best_match
                used_standard_names.add(best_match)
            else:
                # Handle duplicates by creating unique names
                clean_name = self._clean_column_name(col)
                if clean_name in used_standard_names:
                    # Add suffix to make unique
                    counter = 2
                    original_clean = clean_name
                    while clean_name in used_standard_names:
                        clean_name = f"{original_clean}_{counter}"
                        counter += 1
                
                column_mapping[col] = clean_name
                used_standard_names.add(clean_name)
        
        # Apply mapping
        standardized_df = standardized_df.rename(columns=column_mapping)
        print(f"[DEBUG] Column mapping applied: {column_mapping}")
        
        # Verify no duplicates exist
        duplicate_columns = standardized_df.columns[standardized_df.columns.duplicated()]
        if len(duplicate_columns) > 0:
            print(f"[WARNING] Duplicate columns detected after mapping: "
                  f"{duplicate_columns.tolist()}")
            # Force unique column names
            standardized_df.columns = pd.Index([
                f"{col}_{i}" if col in duplicate_columns else col
                for i, col in enumerate(standardized_df.columns)
            ])
        
        return standardized_df
    
    def _find_best_column_match(self, column: str, patterns: Dict[str, list]) -> str:
        """Find the best matching standard column name."""
        col_lower = column.lower().strip()
        best_match = None
        max_score = 0
        
        for standard_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                score = self._calculate_similarity_score(pattern.lower(), col_lower)
                if score > max_score and score > 0.4:  # Threshold
                    max_score = score
                    best_match = standard_name
        
        return best_match
    
    def _calculate_similarity_score(self, pattern: str, column: str) -> float:
        """Calculate similarity score between pattern and column."""
        col_clean = column.replace(' ', '').replace('_', '')
        pattern_clean = pattern.replace(' ', '').replace('_', '')
        
        if pattern == column:
            return 1.0  # Perfect match
        elif pattern_clean == col_clean:
            return 0.95  # Perfect match ignoring spaces/underscores
        elif pattern in column:
            return 0.8 + (len(pattern) / len(column)) * 0.1
        elif column in pattern:
            return 0.6 + (len(column) / len(pattern)) * 0.1
        elif self._fuzzy_match(pattern, column):
            return 0.5
        else:
            return 0
    
    def _fuzzy_match(self, pattern: str, column: str) -> bool:
        """Simple fuzzy matching for column names."""
        pattern_words = set(pattern.replace('_', ' ').split())
        column_words = set(column.replace('_', ' ').split())
        
        overlap = len(pattern_words.intersection(column_words))
        total_words = len(pattern_words.union(column_words))
        
        return (overlap / total_words) > 0.5 if total_words > 0 else False
    
    def _clean_column_name(self, column: str) -> str:
        """Clean column name for consistency."""
        clean_name = column.replace('.', '').replace('(', '').replace(')', '')
        clean_name = clean_name.replace('  ', ' ').strip()
        return clean_name.title().replace(' ', '_')
    
    def clean_json_intelligently(self, json_content: str) -> str:
        """Clean JSON content using pattern recognition."""
        patterns = [
            (r'"\s*\n\s*([^"]*)"', r'"\1"'),
            (r'"\s*\n\s*"', r'""'),
            (r'",\s*\n\s*"', r'", "'),
            (r'"\s*([^"]*?)\s*"', r'"\1"'),
            (r'"([^"]*?)\s{2,}([^"]*?)"', r'"\1 \2"'),
        ]
        
        cleaned = json_content
        for pattern, replacement in patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned
    
    def parse_csv_from_response(self, content: str) -> Tuple[bool, pd.DataFrame]:
        """Parse CSV data from AI response content - enhanced to handle markdown formatting."""
        try:
            print(f"[DEBUG] Parsing AI response for direct CSV format")
            
            # Clean content and remove markdown formatting
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                lines = content.split('\n')
                # Remove first line with ``` and any language specifier
                if lines[0].strip().startswith('```'):
                    lines = lines[1:]
                # Remove last line with ``` if present
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                content = '\n'.join(lines)
                print(f"[DEBUG] Removed markdown code blocks from response")
            
            # Try to parse entire cleaned content as CSV first
            try:
                dataframe = pd.read_csv(io.StringIO(content))
                if len(dataframe) > 0:
                    print(f"[DEBUG] Successfully parsed cleaned content as CSV: {dataframe.shape}")
                    print(f"[DEBUG] CSV columns: {list(dataframe.columns)}")
                    return True, dataframe
            except Exception as e:
                print(f"[DEBUG] Cleaned content CSV parsing failed: {e}")
            
            # Look for CSV table by lines - enhanced detection
            lines = content.split('\n')
            csv_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and markdown remnants
                if not line or line.startswith('```') or line.startswith('**'):
                    continue
                    
                # Look for CSV headers or data rows
                if ',' in line and any(keyword in line.lower() for keyword in [
                    'requirements', 'no,clause', 'identified values', 'gfa', 'hs area', 'parameter',
                    'compliance status', 'reference drawing', 'notes'
                ]):
                    csv_lines.append(line)
                elif csv_lines and ',' in line and len(line.split(',')) >= 8:
                    csv_lines.append(line)
            
            if csv_lines:
                csv_content = '\n'.join(csv_lines)
                print(f"[DEBUG] Found CSV lines: {len(csv_lines)}")
                print(f"[DEBUG] First CSV line: {csv_lines[0] if csv_lines else 'None'}")
                
                # Parse CSV content
                dataframe = pd.read_csv(io.StringIO(csv_content))
                print(f"[DEBUG] CSV parsing successful: shape={dataframe.shape}")
                return True, dataframe
            
            return False, pd.DataFrame()
            
        except Exception as exception:
            print(f"[ERROR] CSV parsing failed: {exception}")
            print(f"[DEBUG] Content preview: {content[:200]}...")
            return False, pd.DataFrame()
    
    def get_compliance_metrics(self, comparisons_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate compliance metrics from comparison DataFrame."""
        try:
            # Validate DataFrame
            if comparisons_df is None or comparisons_df.empty:
                print("[DEBUG] Empty comparisons_df passed to get_compliance_metrics")
                return {
                    'total_parameters': 0,
                    'compliant': 0,
                    'non_compliant': 0,
                    'not_found': 0,
                    'compliance_rate': 0,
                    'non_compliance_rate': 0,
                    'not_found_rate': 0
                }
            
            # Check if required column exists - updated for new format
            compliance_col = None
            if 'Compliance (Y/N)' in comparisons_df.columns:
                compliance_col = 'Compliance (Y/N)'
            elif 'Compliance_Status' in comparisons_df.columns:
                compliance_col = 'Compliance_Status'
            
            if compliance_col is None:
                print(f"[DEBUG] Missing compliance column. Available columns: {list(comparisons_df.columns)}")
                return {
                    'total_parameters': len(comparisons_df),
                    'compliant': 0,
                    'non_compliant': 0,
                    'not_found': 0,
                    'compliance_rate': 0,
                    'non_compliance_rate': 0,
                    'not_found_rate': 0
                }
            
            total = len(comparisons_df)
            
            # Safe pandas filtering with the correct column name
            try:
                if compliance_col == 'Compliance (Y/N)':
                    compliant = len(comparisons_df[comparisons_df[compliance_col] == 'Y'])
                    non_compliant = len(comparisons_df[comparisons_df[compliance_col] == 'N'])
                    not_found = 0  # Y/N format doesn't have "Not Found"
                else:
                    compliant = len(comparisons_df[comparisons_df[compliance_col] == 'Compliant'])
                    non_compliant = len(comparisons_df[comparisons_df[compliance_col] == 'Non-Compliant'])
                    not_found = len(comparisons_df[comparisons_df[compliance_col] == 'Not Found'])
            except Exception as e:
                print(f"[DEBUG] Error in compliance filtering: {e}")
                compliant = 0
                non_compliant = 0
                not_found = 0
            
            return {
                'total_parameters': total,
                'compliant': compliant,
                'non_compliant': non_compliant,
                'not_found': not_found,
                'compliance_rate': (compliant / total * 100) if total > 0 else 0,
                'non_compliance_rate': (non_compliant / total * 100) if total > 0 else 0,
                'not_found_rate': (not_found / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            print(f"[ERROR] get_compliance_metrics failed: {str(e)}")
            print(f"[DEBUG] DataFrame info: shape={comparisons_df.shape if comparisons_df is not None else 'None'}")
            if comparisons_df is not None and not comparisons_df.empty:
                print(f"[DEBUG] Columns: {list(comparisons_df.columns)}")
                print(f"[DEBUG] First few rows:\n{comparisons_df.head()}")
            
            return {
                'total_parameters': 0,
                'compliant': 0,
                'non_compliant': 0,
                'not_found': 0,
                'compliance_rate': 0,
                'non_compliance_rate': 0,
                'not_found_rate': 0
            }