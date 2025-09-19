"""
Data Processor for Drawing Analysis
Handles data parsing, standardization, and DataFrame operations.
"""
import json
import re
import io
import pandas as pd
from typing import Dict, Any, Tuple


class DataProcessor:
    """Processes and standardizes data for drawing analysis."""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        
    def load_parameters_from_json(self, json_path: str) -> pd.DataFrame:
        """Convert JSON parameters to DataFrame format."""
        with open(json_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        parameters = []
        param_templates = json_data.get('parameters', {}).get('parameter_templates', {})
        
        for param_name, param_info in param_templates.items():
            param_dict = {
                'parameter': param_name,
                'description': param_info.get('description', ''),
                'value': param_info.get('value', ''),
                'unit': param_info.get('unit', ''),
                'type': param_info.get('type', ''),
                'source': param_info.get('source', '')
            }
            
            # Add any additional fields from JSON
            for key, value in param_info.items():
                if key not in param_dict:
                    param_dict[key] = value
                    
            parameters.append(param_dict)
        
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
            'Required_Value': ['required value', 'minimum value', 'standard value', 'target value'],
            'Compliance_Status': ['compliance', 'status', 'result', 'compliant', 'pass/fail'],
            'Reference_Drawing': ['reference', 'drawing', 'source', 'ref', 'plan reference'],
            'Notes': ['notes', 'remarks', 'comments', 'observations', 'analysis'],
            'Method': ['method', 'approach', 'technique', 'detection method']
        }
        
        # Merge patterns
        all_patterns = {**universal_patterns, **domain_patterns}
        
        # Create mapping
        column_mapping = {}
        for col in standardized_df.columns:
            best_match = self._find_best_column_match(col, all_patterns)
            if best_match:
                column_mapping[col] = best_match
            else:
                column_mapping[col] = self._clean_column_name(col)
        
        # Apply mapping
        standardized_df = standardized_df.rename(columns=column_mapping)
        print(f"[DEBUG] Column mapping applied: {column_mapping}")
        
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
        """Parse CSV data from AI response content."""
        try:
            lines = content.split('\n')
            csv_lines = []
            
            for line in lines:
                line = line.strip()
                # Look for CSV-like content
                if any(header in line.lower() for header in [
                    'parameter,', 'no,clause,', 'no,parameter', 'clause,parameter'
                ]):
                    csv_lines.append(line)
                elif csv_lines and (',' in line and len(line.split(',')) >= 4):
                    csv_lines.append(line)
                elif csv_lines and line == '':
                    continue
                elif csv_lines and not line:
                    break
            
            if not csv_lines:
                return False, pd.DataFrame()
            
            csv_content = '\n'.join(csv_lines)
            dataframe = pd.read_csv(io.StringIO(csv_content))
            
            return True, dataframe
            
        except Exception as exception:
            print(f"[ERROR] CSV parsing failed: {exception}")
            return False, pd.DataFrame()
    
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