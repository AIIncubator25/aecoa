"""
Agent 1: Unified Document Processor - CSV/TXT/XLS to YAML + JSON Converter
Converts building regulation clauses from various formats into structured YAML specifications
and automatically generates machine-readable JSON parameters with JsonLogic rules.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import json
import re
import yaml
from pathlib import Path
import zipfile
import io
from datetime import datetime

# Install jsonlogic if not present
try:
    import json_logic
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "json-logic-py"])
    import json_logic


class JsonParameterGenerator:
    """Generates JSON parameters with JsonLogic from YAML specifications."""
    
    def __init__(self):
        self.json_output = {}
        self.jsonlogic_rules = []
        self.validation_errors = []
    
    def generate_json_from_yaml(self, yaml_content: str, filename: str) -> Dict[str, Any]:
        """
        Generate comprehensive JSON parameters with JsonLogic from YAML content.
        
        Args:
            yaml_content: The YAML specification content
            filename: Name of the source file
            
        Returns:
            Dict containing JSON parameters, JsonLogic rules, and metadata
        """
        try:
            # Parse YAML content
            yaml_data = yaml.safe_load(yaml_content)
            
            if not yaml_data:
                return self._create_error_response("Empty YAML content")

            # Extract the main clause (first key in YAML)
            clause_key = list(yaml_data.keys())[0]
            clause_data = yaml_data[clause_key]
            
            # Generate JSON structure
            json_result = self._build_json_structure(clause_key, clause_data, filename)
            
            return {
                'success': True,
                'json_content': json_result,
                'jsonlogic_rules': json_result.get('jsonlogic_rules', []),
                'filename': filename,
                'validation_errors': self.validation_errors
            }
            
        except yaml.YAMLError as e:
            return self._create_error_response(f"YAML parsing error: {str(e)}")
        except Exception as e:
            return self._create_error_response(f"JSON generation error: {str(e)}")
    
    def _build_json_structure(self, clause_key: str, clause_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Build the comprehensive JSON structure from YAML data."""
        
        json_structure = {
            "metadata": {
                "clause_id": clause_key,
                "source_file": filename,
                "generated_timestamp": pd.Timestamp.now().isoformat(),
                "description": clause_data.get('description', '').strip(),
                "references": clause_data.get('references', {}),
                "units": clause_data.get('units', {})
            },
            "parameters": self._extract_parameters(clause_data),
            "tables": self._extract_tables(clause_data),
            "compliance_rules": self._extract_compliance_rules(clause_data),
            "jsonlogic_rules": self._extract_jsonlogic_rules(clause_data),
            "csv_schema": self._extract_csv_schema(clause_data),
            "validation": {
                "unit_checks": clause_data.get('unit_checks', {}),
                "evaluation_notes": clause_data.get('evaluation_notes', [])
            }
        }
        
        return json_structure
    
    def _extract_parameters(self, clause_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure parameter information."""
        parameters = {
            "inputs_expected": clause_data.get('inputs_expected', []),
            "parameter_templates": {}
        }
        
        # Process parameter templates
        templates = clause_data.get('parameter_templates', {})
        for param_name, param_config in templates.items():
            parameters["parameter_templates"][param_name] = {
                "name": param_name,
                "pattern": param_config.get('pattern', '.*'),
                "unit_conversion": param_config.get('unit_conversion', {}),
                "source": param_config.get('source', {}),
                "category": param_config.get('unit_conversion', {}).get('category', 'unknown'),
                "unit": param_config.get('unit_conversion', {}).get('unit', ''),
                "to_canonical": param_config.get('unit_conversion', {}).get('to_canonical', 1.0),
                "description": param_config.get('source', {}).get('description', '')
            }
        
        return parameters
    
    def _extract_tables(self, clause_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure table information."""
        tables = clause_data.get('tables', {})
        structured_tables = {}
        
        for table_name, table_data in tables.items():
            structured_tables[table_name] = {
                "name": table_name,
                "rows": table_data.get('rows', []),
                "columns": self._extract_table_columns(table_data.get('rows', [])),
                "row_count": len(table_data.get('rows', []))
            }
        
        return structured_tables
    
    def _extract_table_columns(self, rows: List[Dict[str, Any]]) -> List[str]:
        """Extract column names from table rows."""
        columns = set()
        for row in rows:
            columns.update(row.keys())
        return list(columns)
    
    def _extract_compliance_rules(self, clause_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and structure compliance rules."""
        rules = clause_data.get('compliance_rules', [])
        structured_rules = []
        
        for rule in rules:
            structured_rule = {
                "name": rule.get('name', ''),
                "description": rule.get('description', ''),
                "type": self._determine_rule_type(rule),
                "severity": rule.get('severity', 'info'),
                "reference": rule.get('reference', ''),
                "field": rule.get('field', ''),
                "operator": rule.get('operator', ''),
                "value": rule.get('value'),
                "unit": rule.get('unit', ''),
                "match_table": rule.get('match_table', ''),
                "match_on": rule.get('match_on', ''),
                "compare": rule.get('compare', {}),
                "applies_when": rule.get('applies_when', {}),
                "note": rule.get('note', '')
            }
            structured_rules.append(structured_rule)
        
        return structured_rules
    
    def _determine_rule_type(self, rule: Dict[str, Any]) -> str:
        """Determine the type of compliance rule."""
        if rule.get('operator') == 'copy':
            return 'parameter_population'
        elif rule.get('operator') == 'defined':
            return 'information'
        elif rule.get('match_table'):
            return 'table_lookup'
        elif rule.get('value') is not None:
            return 'direct_comparison'
        else:
            return 'custom'
    
    def _extract_jsonlogic_rules(self, clause_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and structure JsonLogic rules."""
        jsonlogic_rules = clause_data.get('jsonlogic_rules', {})
        structured_rules = []
        
        # Handle both dict and list formats
        if isinstance(jsonlogic_rules, dict):
            # Convert dict format to list
            for rule_name, rule_content in jsonlogic_rules.items():
                structured_rule = {
                    "name": rule_name,
                    "description": f"JsonLogic rule: {rule_name}",
                    "rule": rule_content,
                    "reference": "",
                    "severity": "error",
                    "rule_type": self._determine_jsonlogic_type(rule_content),
                    "variables_used": self._extract_variables_from_rule(rule_content)
                }
                structured_rules.append(structured_rule)
        elif isinstance(jsonlogic_rules, list):
            # Handle list format
            for rule in jsonlogic_rules:
                structured_rule = {
                    "name": rule.get('name', ''),
                    "description": rule.get('description', ''),
                    "rule": rule.get('rule', {}),
                    "reference": rule.get('reference', ''),
                    "severity": rule.get('severity', 'error'),
                    "rule_type": self._determine_jsonlogic_type(rule.get('rule', {})),
                    "variables_used": self._extract_variables_from_rule(rule.get('rule', {}))
                }
                structured_rules.append(structured_rule)
        
        return structured_rules
    
    def _determine_jsonlogic_type(self, rule: Dict[str, Any]) -> str:
        """Determine the type of JsonLogic rule."""
        try:
            if not rule or not isinstance(rule, dict):
                return 'empty'
            
            # Convert dict_keys to list to avoid subscriptable issues
            operators = list(rule.keys())
            if not operators:
                return 'empty'
            
            main_op = operators[0]
            if main_op in ['>=', '<=', '>', '<', '==', '!=']:
                return 'comparison'
            elif main_op in ['and', 'or']:
                return 'logical'
            elif main_op == 'if':
                return 'conditional'
            elif main_op == 'in':
                return 'membership'
            else:
                return 'complex'
        except Exception:
            return 'unknown'
    
    def _extract_variables_from_rule(self, rule: Dict[str, Any]) -> List[str]:
        """Extract variable names used in JsonLogic rule."""
        variables = set()
        
        def extract_vars(obj):
            try:
                if isinstance(obj, dict):
                    if 'var' in obj:
                        variables.add(str(obj['var']))  # Ensure string conversion
                    else:
                        for value in obj.values():
                            extract_vars(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_vars(item)
            except Exception:
                # Skip problematic structures
                pass
        
        try:
            extract_vars(rule)
            return sorted(list(variables))  # Return sorted list for consistency
        except Exception:
            return []
    
    def _extract_csv_schema(self, clause_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CSV schema information."""
        csv_schema = clause_data.get('csv_schema', {})
        return {
            "columns_pretty": csv_schema.get('columns_pretty', []),
            "columns": csv_schema.get('columns', []),
            "rows": csv_schema.get('rows', []),
            "row_count": len(csv_schema.get('rows', []))
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response structure."""
        return {
            'success': False,
            'error': error_message,
            'json_content': {},
            'jsonlogic_rules': [],
            'validation_errors': [error_message]
        }


# Agent 0's Default Prompt - Clause to YAML Converter with Reference Template
DEFAULT_PROMPT = """SYSTEM
You are an expert AEC (Architecture, Engineering, Construction) compliance specialist and YAML structure designer. Your mission is to convert building regulation clauses from CSV/TXT/XLS formats into comprehensive, machine-readable YAML specifications.

REFERENCE TEMPLATE (from 2.10_HS_Beneath_Staircase.yaml):
Use this exact structure pattern, adapting the content for your specific clause:

```yaml
[CLAUSE_ID]_[CLAUSE_NAME]:
  description: >
    [Requirements description]

  references:
    clause: "[clause number]"
    figures: ["Figure X.X"]
    tables: ["Table X.X.X"]

  units:
    length_mm: "millimetres"
    area_m2: "square metres"
    volume_m3: "cubic metres"
    count: "number"
    percentage: "percent"

  # Runtime inputs Step 1 UI must provide
  inputs_expected:
    - [parameter_1]     # Description
    - [parameter_2]     # More parameters from document

  # Parameter templates (measured and table-derived)
  parameter_templates:
    # ---- Measured (user inputs) ----
    parameter_name_example:
      pattern: ".*"
      unit_conversion: {category: "length", unit: "mm", to_canonical: 0.001}
      source: {description: "Example parameter description"}
    
    # ---- Table-derived (populated via compliance_rules) ----
    derived_parameter_example:
      pattern: ".*" 
      unit_conversion: {category: "area", unit: "m²", to_canonical: 1.0}
      source: {description: "Example derived parameter from table"}

PARAMETER TEMPLATE CATEGORIES TO USE:
- category: "length" (for dimensions, thicknesses, clearances) - unit: "mm", to_canonical: 0.001  
- category: "area" (for floor areas, surface areas) - unit: "m²", to_canonical: 1.0
- category: "volume" (for room volumes, capacities) - unit: "m³", to_canonical: 1.0
- category: "count" (for quantities, numbers) - unit: "number", to_canonical: 1.0
- category: "percentage" (for ratios, percentages) - unit: "%", to_canonical: 0.01
- category: "text" (for descriptions, types) - unit: "text", to_canonical: 1.0

  # Tables from document
  tables:
    table_name_example:
      rows:
        - range: {lt: 40}                   # condition < value
          min_area_m2: 1.44
          min_volume_m3: 3.6
        - range: {gt: 40, lt: 75}          # value < condition < value  
          min_area_m2: 2.2
          min_volume_m3: 5.4
        - range: {gt: 140}                 # condition > value
          min_area_m2: 3.4
          min_volume_m3: 9.0

TABLE RANGE SYNTAX TO USE:
- For "less than": {lt: value}
- For "greater than": {gt: value} 
- For "between": {gt: min_value, lt: max_value}
- For "greater than or equal": {gte: value}
- For "less than or equal": {lte: value}

  # Compliance Rules
  compliance_rules:
    # Info guards for special methods
    - name: "Area counting method guidance"
      description: "Only floor area with clear height ≥ 1500 mm is counted for minimum area"
      field: "hs_area_clear_ge_1500_mm_m2"
      operator: "defined"
      severity: "info"
      reference: "2.10(a)"

    # Populate table-derived parameters
    - name: "Populate minimum floor area by GFA"
      reference: "Table 2.2.1(b)"
      match_table: "tables.min_requirements_by_gfa"
      match_on: "inputs_expected.gfa_m2"
      compare:
        field: "hs_min_floor_area_m2"
        against_table_field: "min_hs_floor_area_m2"
        operator: "copy"

    # Compliance checks (measured vs required)
    - name: "Minimum HS floor area requirement"
      description: "Counted HS area must meet or exceed table minimum"
      match_table: "tables.min_requirements_by_gfa"
      match_on: "inputs_expected.gfa_m2"
      compare:
        field: "hs_area_clear_ge_1500_mm_m2"
        operator: ">="
        against_table_field: "min_hs_floor_area_m2"
      severity: "error"
      reference: "2.10(a); Table 2.2.1(b)"

    # Direct value comparisons
    - name: "Ceiling slab thickness minimum"
      field: "hs_ceiling_slab_thickness_mm"
      operator: ">="
      value: 300
      unit: "mm"
      severity: "error"
      reference: "2.10(c)"

COMPLIANCE RULE OPERATORS TO USE:
- "defined" - checks if parameter exists
- ">=" - greater than or equal to
- "<=" - less than or equal to  
- "==" - equals
- "!=" - not equals
- "copy" - copies value from table to parameter

  # Provenance
  provenance:
    show_references: true
    include_selected_range: true
    include_source: true

  # Unit validation
  unit_checks:
    [parameter]: "[expected_unit]"

  # CSV schema for export
  csv_schema:
    columns_pretty:
      - "No"
      - "Clause"
      - "Parameter"
      - "Minimum Value"
      - "Maximum Value" 
      - "Unit"
      - "Reference"
      - "Notes"
    columns:
      - no
      - clause
      - parameter
      - min_value
      - max_value
      - unit
      - reference
      - notes
    rows:
      - no: 1
        clause: "2.10(a)"
        parameter: "HS floor area for GFA < 40"
        min_value: 1.44
        max_value: null
        unit: "m²"
        reference: "Table 2.2.1(b)"
        notes: "Only area with clear height ≥ 1500mm counted"
      - no: 2
        clause: "2.10(b)"
        parameter: "HS volume for GFA < 40"
        min_value: 3.6
        max_value: null
        unit: "m³"
        reference: "Table 2.2.1(c)"
        notes: "Entire enclosed volume may be used"
      - no: 3
        clause: "2.10(c)"
        parameter: "HS ceiling slab thickness"
        min_value: 300
        max_value: null
        unit: "mm"
        reference: "2.10(c)"
        notes: "Minimum structural requirement"

  # Evaluation guidance
  evaluation_notes:
    - "Table range matching: Compare parameter values against 'range' conditions (lt, gt, gte, lte) to select applicable table rows"
    - "Boundary handling: For exact boundary values, defer to regulatory authority guidance or use conservative interpretation"
    - "Unit consistency: Ensure all measurements use standard AEC units (mm for lengths, m² for areas, m³ for volumes)"
    - "Conditional requirements: Apply shape-specific rules only when 'applies_when' conditions are met"
    - "Cross-parameter validation: Some parameters depend on others (e.g., area and volume must both satisfy requirements)"
    - "Clear height measurement: For area calculations, measure from finished floor to underside of structural elements"

  # JsonLogic rules (machine-readable for faster processing)
  jsonlogic_rules:
    # Simple value comparisons (direct minimums/maximums)
    - name: "ceiling_slab_thickness_minimum"
      description: "Ceiling slab thickness must be at least 300mm"
      rule: {">=" : [{"var": "hs_ceiling_slab_thickness_mm"}, 300]}
      reference: "2.10(c)"
      severity: "error"
    
    - name: "staircase_waist_thickness_minimum"
      description: "Staircase waist thickness must be at least 300mm"
      rule: {">=" : [{"var": "staircase_waist_thickness_mm"}, 300]}
      reference: "2.10(c)"
      severity: "error"
    
    - name: "ventilation_clearance_minimum"
      description: "Ventilation sleeve clearance must be at least 700mm"
      rule: {">=" : [{"var": "vent_sleeve_wall_clearance_mm"}, 700]}
      reference: "2.10(d)"
      severity: "error"
    
    # Table-based range lookups with GFA conditions
    - name: "minimum_floor_area_gfa_ranges"
      description: "Floor area must meet table requirements based on GFA range"
      rule: {"or": [
        {"and": [{"<": [{"var": "gfa_m2"}, 40]}, {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, 1.44]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 40]}, {"<": [{"var": "gfa_m2"}, 45]}, {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, 1.60]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 45]}, {"<": [{"var": "gfa_m2"}, 75]}, {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, 2.20]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 75]}, {"<": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, 2.80]}]},
        {"and": [{">": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, 3.40]}]}
      ]}
      reference: "Table 2.2.1(b)"
      severity: "error"
    
    - name: "minimum_volume_gfa_ranges"
      description: "Volume must meet table requirements based on GFA range"
      rule: {"or": [
        {"and": [{"<": [{"var": "gfa_m2"}, 40]}, {">=": [{"var": "hs_enclosed_volume_m3"}, 3.6]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 40]}, {"<": [{"var": "gfa_m2"}, 45]}, {">=": [{"var": "hs_enclosed_volume_m3"}, 3.6]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 45]}, {"<": [{"var": "gfa_m2"}, 75]}, {">=": [{"var": "hs_enclosed_volume_m3"}, 5.4]}]},
        {"and": [{">=": [{"var": "gfa_m2"}, 75]}, {"<": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_enclosed_volume_m3"}, 7.2]}]},
        {"and": [{">": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_enclosed_volume_m3"}, 9.0]}]}
      ]}
      reference: "Table 2.2.1(c)"
      severity: "error"
    
    # Conditional requirements (shape-dependent)
    - name: "square_unit_check_for_irregular_shapes"
      description: "Square unit validation for trapezoidal/L-shaped HS"
      rule: {"if": [
        {"in": [{"var": "hs_shape"}, ["trapezoidal", "L-shaped", "L_shaped"]]},
        {"or": [
          {"and": [{"<": [{"var": "gfa_m2"}, 40]}, {">=": [{"var": "hs_square_units_0_6m"}, 3]}]},
          {"and": [{">=": [{"var": "gfa_m2"}, 40]}, {"<": [{"var": "gfa_m2"}, 45]}, {">=": [{"var": "hs_square_units_0_6m"}, 3]}]},
          {"and": [{">=": [{"var": "gfa_m2"}, 45]}, {"<": [{"var": "gfa_m2"}, 75]}, {">=": [{"var": "hs_square_units_0_6m"}, 4]}]},
          {"and": [{">=": [{"var": "gfa_m2"}, 75]}, {"<": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_square_units_0_6m"}, 5]}]},
          {"and": [{">": [{"var": "gfa_m2"}, 140]}, {">=": [{"var": "hs_square_units_0_6m"}, 6]}]}
        ]},
        true
      ]}
      reference: "Table 2.2.1(c)"
      severity: "error"
    
    # Cross-parameter validation
    - name: "consistency_check_area_volume"
      description: "Both area and volume requirements must be satisfied simultaneously"
      rule: {"and": [
        {">=": [{"var": "hs_area_clear_ge_1500_mm_m2"}, {"var": "hs_min_floor_area_m2"}]},
        {">=": [{"var": "hs_enclosed_volume_m3"}, {"var": "hs_min_volume_m3"}]}
      ]}
      reference: "2.10(a), 2.10(b)"
      severity: "error"

JSONLOGIC OPERATORS TO USE:
- Simple: ">=", "<=", "==", "!=", ">", "<"
- Logical: "and", "or", "!"
- Conditional: "if" (condition, then, else)
- Array: "in" (value, array), "map", "filter"
- Variables: {"var": "parameter_name"}
```

USER
Input Document Content:
{document_content}

ANALYSIS INSTRUCTIONS:

Your task is to analyze the provided document and create YAML following the REFERENCE TEMPLATE structure above:

1. **CLAUSE IDENTIFICATION**: Extract clause number, title, and overall scope from document

2. **PARAMETER EXTRACTION**: Identify ALL measurable parameters including:
   - Dimensions (lengths, areas, volumes, thicknesses, clearances)
   - Quantities (counts, percentages, ratios)
   - Material properties (strengths, densities, grades)
   - Performance criteria (minimums, maximums, allowable ranges)
   - Conditional parameters (shape-dependent, use-dependent)

3. **TABLE PROCESSING**: Convert ALL tabular data into structured tables with:
   - Proper range conditions (lt, gt, combined ranges)
   - All column values preserved with correct data types
   - Logical table grouping by key parameters

4. **COMPLIANCE RULES GENERATION**: Create comprehensive rules including:
   - Parameter population from tables (copy operations)
   - Compliance checking (measured vs required values)
   - Conditional requirements (applies_when clauses)
   - Direct value validations (fixed minimums/maximums)
   - Cross-parameter relationships

5. **UNIT STANDARDIZATION**: Convert all units to standard AEC units:
   - Lengths: mm (millimeters)
   - Areas: m² (square meters)
   - Volumes: m³ (cubic meters)
   - Percentages: % (percent)
   - Counts: number (count)

6. **JSONLOGIC RULES GENERATION**: Create machine-readable JsonLogic rules for:
   - Simple value comparisons (>=, <=, ==, !=)
   - Range validations using table lookups
   - Conditional requirements with "if-then" logic
   - Complex "and/or" combinations for multi-parameter checks
   - Proper error handling and reference tracking

7. **CSV SCHEMA GENERATION**: Create a structured export table containing:
   - All key parameters as rows with sequential numbering
   - Requirements and values as columns (include min_value, max_value, unit, reference, notes)
   - Proper headers for both display (columns_pretty) and machine processing (columns)
   - Complete coverage of document content including conditional and derived parameters
   - Notes column for special conditions, measurement guidance, and regulatory context

8. **JSONLOGIC RULES GENERATION**: Create comprehensive machine-readable JsonLogic rules for:
   - Simple value comparisons (>=, <=, ==, !=) for direct minimums and maximums
   - Complex range validations using GFA-based table lookups with "or" combinations
   - Conditional requirements with "if-then" logic for shape-dependent or use-dependent rules
   - Cross-parameter validation ensuring multiple requirements are satisfied simultaneously
   - Proper error handling, severity classification (error/warning/info), and reference tracking

CRITICAL REQUIREMENTS:
- Follow the REFERENCE TEMPLATE structure exactly
- Extract EVERY parameter and requirement from the document
- Create proper range-based table lookups
- Generate complete compliance rule sets
- Preserve all regulatory references and notes
- Ensure YAML syntax validity

Generate the complete YAML output following the reference structure."""


class UnifiedDocumentProcessor:
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.prompt = DEFAULT_PROMPT
        self.prompt_log = []
        self.response_log = []
        self.debug_log = []   # Store debug information
        
        # Custom prompts (can be set via UI)
        self.custom_combined_prompt = None
        self.custom_system_prompt = None
        self.custom_user_prompt = None
    
    def _test_network_connectivity(self) -> Dict[str, bool]:
        """Test network connectivity to different API endpoints."""
        import requests
        
        endpoints = {
            'GovTech': 'https://llmaas.govtext.gov.sg',
            'OpenAI': 'https://api.openai.com',
            'Ollama': 'http://localhost:11434'
        }
        
        connectivity = {}
        for name, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                connectivity[name] = True
            except Exception:
                connectivity[name] = False
        
        return connectivity
    
    def _log_debug(self, message: str):
        """Log debug messages for troubleshooting."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        debug_entry = f"[{timestamp}] {message}"
        self.debug_log.append(debug_entry)
        print(debug_entry)  # Also print to console for immediate visibility
    
    def _clean_yaml_response(self, yaml_content: str) -> str:
        """Clean AI response by removing markdown code fences and extra content."""
        if not yaml_content:
            return yaml_content
        
        yaml_content = yaml_content.strip()
        
        # Handle multiple code blocks - find the actual YAML block
        # Look for patterns like ```yaml or ```yml at start of lines
        lines = yaml_content.split('\n')
        yaml_start_idx = None
        yaml_end_idx = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith('```yaml') or line_stripped.startswith('```yml'):
                yaml_start_idx = i + 1
            elif yaml_start_idx is not None and line_stripped == '```':
                yaml_end_idx = i
                break
        
        # If we found YAML block delimiters, extract just that content
        if yaml_start_idx is not None:
            if yaml_end_idx is not None:
                yaml_content = '\n'.join(lines[yaml_start_idx:yaml_end_idx])
            else:
                # No closing fence found, take everything after opening fence
                yaml_content = '\n'.join(lines[yaml_start_idx:])
        
        # Fallback: simple cleanup for cases without proper fencing
        else:
            # Remove leading/trailing code fences
            if yaml_content.startswith('```yaml'):
                yaml_content = yaml_content[7:].strip()
            elif yaml_content.startswith('```yml'):
                yaml_content = yaml_content[6:].strip()
            elif yaml_content.startswith('```'):
                yaml_content = yaml_content[3:].strip()
            
            if yaml_content.endswith('```'):
                yaml_content = yaml_content[:-3].strip()
        
        return yaml_content.strip()
    
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent (compatibility with app.py)."""
        return {"user": DEFAULT_PROMPT}
    
    
    def set_custom_prompts(self, combined_prompt: str = None, 
                          system_prompt: str = None, user_prompt: str = None):
        """Set custom prompts for specialized parsing needs."""
        self.custom_combined_prompt = combined_prompt
        self.custom_system_prompt = system_prompt
        self.custom_user_prompt = user_prompt
    
    def parse_document_to_yaml(self, file_content: bytes, filename: str, 
                              api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Parse uploaded document (CSV/TXT/XLS) into YAML format using AI."""
        
        try:
            # ENHANCED DEBUG: Log entry point
            self._log_debug(f"parse_document_to_yaml: Starting with filename={filename}, content_size={len(file_content)}")
            
            # Convert file content to text based on file type
            try:
                self._log_debug("parse_document_to_yaml: Calling _extract_text_from_file")
                document_text = self._extract_text_from_file(file_content, filename)
                self._log_debug(f"parse_document_to_yaml: Text extraction successful, length={len(document_text) if document_text else 0}")
            except Exception as extract_error:
                error_msg = f"Document parsing failed: {str(extract_error)}"
                self._log_debug(f"parse_document_to_yaml: Text extraction failed - {error_msg}")
                return False, {"error": error_msg}
            
            if not document_text:
                return False, {"error": "Could not extract text from the uploaded file"}
            
            # Use AI to convert to YAML
            try:
                self._log_debug("parse_document_to_yaml: Calling _convert_with_ai")
                success, result = self._convert_with_ai(document_text, api_key)
                self._log_debug(f"parse_document_to_yaml: AI conversion result - success={success}")
            except Exception as ai_error:
                error_msg = f"AI conversion failed: {str(ai_error)}"
                self._log_debug(f"parse_document_to_yaml: AI conversion failed - {error_msg}")
                return False, {"error": error_msg}
            
            if success:
                # Validate and clean the YAML output
                yaml_content = result.get('yaml_content', '')
                if yaml_content:
                    # Clean any remaining template placeholders that might cause parsing issues
                    yaml_content = self._clean_yaml_placeholders(yaml_content)
                    
                    # Clean JsonLogic rules to prevent dict_keys issues
                    yaml_content = self._clean_yaml_jsonlogic_rules(yaml_content)
                    
                    # Validate YAML syntax
                    try:
                        yaml.safe_load(yaml_content)
                        return True, {
                            'yaml_content': yaml_content,
                            'document_preview': document_text,  # Show full content
                            'conversion_method': 'AI',
                            'filename': filename,
                            'jsonlogic_validated': self._validate_jsonlogic_rules(yaml_content)
                        }
                    except yaml.YAMLError as e:
                        # Enhanced error reporting with YAML content preview
                        error_lines = yaml_content.split('\n')[:10]  # First 10 lines
                        error_preview = '\n'.join(error_lines)
                        self._log_debug(f"YAML parsing failed. Error: {str(e)}")
                        self._log_debug(f"YAML content preview:\n{error_preview}")
                        
                        return False, {
                            "error": (f"Generated YAML has syntax errors: {str(e)}\n\n"
                                     f"YAML preview:\n{error_preview}")
                        }
                else:
                    return False, {"error": "AI did not generate YAML content"}
            else:
                return False, result
                
        except Exception as e:
            return False, {"error": f"Document parsing failed: {str(e)}"}
    
    def _extract_text_from_file(self, file_content: bytes, filename: str) -> str:
        """Extract text content from various file formats."""
        file_ext = Path(filename).suffix.lower()
        
        try:
            if file_ext == '.csv':
                # Handle CSV files with robust parsing for irregular formats
                import io
                try:
                    # First try standard CSV parsing
                    df = pd.read_csv(io.BytesIO(file_content))
                    return self._dataframe_to_text(df, "CSV")
                except pd.errors.ParserError:
                    # Fallback: Handle irregular CSV by reading as text lines
                    try:
                        text_content = file_content.decode('utf-8')
                        return self._process_irregular_csv_text(text_content)
                    except UnicodeDecodeError:
                        text_content = file_content.decode('latin-1')
                        return self._process_irregular_csv_text(text_content)
                except Exception as e:
                    # Additional fallback for any other CSV parsing issues
                    try:
                        text_content = file_content.decode('utf-8')
                        return f"=== CSV PARSING ERROR FALLBACK ===\n" \
                               f"Error: {str(e)}\n" \
                               f"Raw content (first 1000 chars):\n{text_content[:1000]}"
                    except:
                        return f"=== CSV PARSING ERROR ===\nCould not parse CSV file: {str(e)}"
                
            elif file_ext in ['.xlsx', '.xls']:
                # Handle Excel files
                import io
                df = pd.read_excel(io.BytesIO(file_content))
                return self._dataframe_to_text(df, "Excel")
                
            elif file_ext == '.txt':
                # Handle text files
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    return file_content.decode('latin-1')
            else:
                # Try to decode as text
                try:
                    return file_content.decode('utf-8')
                except UnicodeDecodeError:
                    return file_content.decode('latin-1')
                    
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def _process_irregular_csv_text(self, text_content: str) -> str:
        """Process irregular CSV content as plain text when pandas parsing fails."""
        lines = text_content.strip().split('\n')
        processed_text = "=== CSV TEXT CONTENT (Irregular Format) ===\n\n"
        
        for i, line in enumerate(lines[:50]):  # Limit to first 50 lines
            cleaned_line = line.replace('[', '').replace(']', '').strip()
            processed_text += f"Line {i+1}: {cleaned_line}\n"
            
        if len(lines) > 50:
            processed_text += f"\n... ({len(lines) - 50} additional lines truncated)\n"
            
        return processed_text
    
    def _dataframe_to_text(self, df: pd.DataFrame, file_type: str) -> str:
        """Convert DataFrame to structured text for AI processing."""
        try:
            text_parts = [f"=== {file_type} DOCUMENT CONTENT ===\n"]
            
            # Add basic info
            text_parts.append(f"Rows: {len(df)}, Columns: {len(df.columns)}\n")
            text_parts.append(f"Column Names: {', '.join(df.columns.astype(str))}\n\n")
            
            # Add the data in a structured format
            text_parts.append("=== DATA CONTENT ===")
            
            # Convert to string representation preserving structure
            for idx, row in df.iterrows():
                row_text = []
                for col in df.columns:
                    try:
                        value = row[col]
                        if pd.notna(value) and str(value).strip():
                            # Escape any problematic characters
                            col_name = str(col).replace('[', '').replace(']', '')
                            value_str = str(value).replace('[', '').replace(']', '')
                            row_text.append(f"{col_name}: {value_str}")
                    except Exception as e:
                        # Skip problematic columns
                        continue
                
                if row_text:  # Only add rows with content
                    text_parts.append(f"Row {idx + 1}: " + " | ".join(row_text))
            
            # Add table structure analysis with error handling
            text_parts.append(f"\n=== TABLE STRUCTURE ANALYSIS ===")
            
            # Look for numeric patterns that might be tables
            try:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    text_parts.append(f"Numeric columns detected: {', '.join(numeric_cols)}")
            except Exception:
                text_parts.append("Numeric column detection skipped due to data format issues")
            
            # Look for range patterns in text
            try:
                text_content = df.astype(str).values.flatten()
                range_patterns = []
                for text in text_content:
                    text_str = str(text).lower()
                    if any(pattern in text_str for pattern in ['<', '>', 'between', 'from', 'to']):
                        range_patterns.append(str(text))
                
                if range_patterns:
                    text_parts.append("Range patterns found:")
                    for pattern in range_patterns[:10]:  # Limit to first 10
                        text_parts.append(f"  - {pattern}")
            except Exception:
                text_parts.append("Range pattern analysis skipped due to data format issues")
            
            return "\n".join(text_parts)
            
        except Exception as e:
            # Fallback: return basic error info
            return f"=== {file_type} DOCUMENT CONTENT (FALLBACK) ===\n" \
                   f"Error processing DataFrame: {str(e)}\n" \
                   f"DataFrame shape: {df.shape}\n" \
                   f"Columns: {list(df.columns)}"
    
    def _process_irregular_csv_text(self, text_content: str) -> str:
        """Process irregular CSV content as plain text with structure analysis."""
        lines = text_content.strip().split('\n')
        text_parts = ["=== IRREGULAR CSV DOCUMENT CONTENT ===\n"]
        
        text_parts.append(f"Total lines: {len(lines)}\n")
        text_parts.append("=== RAW CONTENT ===")
        
        # Process each line and identify structure
        table_sections = []
        current_table = []
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                if current_table:
                    table_sections.append(current_table)
                    current_table = []
                continue
                
            # Check if line looks like a table header or data
            comma_count = line.count(',')
            if comma_count > 0 and any(char.isdigit() for char in line):
                current_table.append((i, line, 'table_data'))
            elif line.isupper() or 'TABLE' in line.upper():
                if current_table:
                    table_sections.append(current_table)
                    current_table = []
                text_parts.append(f"SECTION HEADER (Line {i}): {line}")
            else:
                text_parts.append(f"Line {i}: {line}")
        
        # Add final table if exists
        if current_table:
            table_sections.append(current_table)
        
        # Process identified tables
        for idx, table in enumerate(table_sections):
            if len(table) > 1:  # Only process if multiple rows
                text_parts.append(f"\n=== IDENTIFIED TABLE {idx + 1} ===")
                for line_num, content, line_type in table:
                    text_parts.append(f"Line {line_num}: {content}")
        
        return "\n".join(text_parts)
    
    def _convert_with_ai(self, document_text: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Convert document text to YAML using AI prompt-response approach."""
        
        try:
            self._log_debug("_convert_with_ai: Starting AI conversion")
            
            # Ensure document_text is a clean string to avoid any pandas dtype issues
            try:
                self._log_debug("_convert_with_ai: Cleaning document text")
                if not isinstance(document_text, str):
                    document_text = str(document_text)
                
                # Remove any problematic characters that might trigger pandas dtype inference
                cleaned_text = document_text.replace('[', '').replace(']', '').replace('category', 'classification')
                self._log_debug(f"_convert_with_ai: Text cleaned, length={len(cleaned_text)}")
                
            except Exception as clean_error:
                self._log_debug(f"_convert_with_ai: Text cleaning failed: {str(clean_error)}")
                cleaned_text = document_text  # fallback to original
            
            # Use custom prompt if available, otherwise default
            try:
                self._log_debug("_convert_with_ai: Formatting prompt")
                
                # Use simple string replacement instead of .format() to avoid pandas dtype inference
                if self.custom_combined_prompt:
                    prompt = self.custom_combined_prompt.replace('{document_content}', cleaned_text)
                elif self.custom_user_prompt:
                    prompt = self.custom_user_prompt.replace('{document_content}', cleaned_text)
                else:
                    prompt = self.prompt.replace('{document_content}', cleaned_text)
                
                self._log_debug(f"_convert_with_ai: Prompt formatted successfully, length={len(prompt)}")
                
            except Exception as format_error:
                error_msg = f"Prompt formatting failed: {str(format_error)}"
                self._log_debug(f"_convert_with_ai: {error_msg}")
                return False, {"error": error_msg}
            
            # Log the prompt - AVOID pandas.Timestamp which can cause 'category' errors
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            
            self.prompt_log.append({
                "prompt": prompt[:1000] + "..." if len(prompt) > 1000 else prompt,
                "document_length": len(document_text),
                "timestamp": timestamp
            })
            
            self._log_debug("_convert_with_ai: Prompt logged successfully")
            
            try:
                # Get provider and model from session state or use defaults
                try:
                    import streamlit as st
                    provider = getattr(st.session_state, 'ai_provider', self.provider)
                    model = getattr(st.session_state, 'ai_model', self.model)
                except:
                    provider = self.provider
                    model = self.model
                
                self._log_debug(f"_convert_with_ai: Using provider={provider}")
                self._log_debug(f"_convert_with_ai: Using model={model}")
                
                # Create API request based on provider
                if provider == "OpenAI":
                    self._log_debug("_convert_with_ai: Calling OpenAI API")
                    success, result = self._call_openai(prompt, api_key, model)
                elif provider == "GovTech":
                    self._log_debug("_convert_with_ai: Calling GovTech API")
                    success, result = self._call_govtech(prompt, api_key, model)
                    
                    # If GovTech fails with connection error, suggest alternatives
                    if not success and "connection failed" in result.get('error', '').lower():
                        connectivity = self._test_network_connectivity()
                        alternative_msg = "\n\nAlternative options:\n"
                        
                        if connectivity.get('OpenAI', False):
                            alternative_msg += "• ✅ OpenAI API appears accessible - consider switching to OpenAI provider\n"
                        else:
                            alternative_msg += "• ❌ OpenAI API also not accessible\n"
                            
                        if connectivity.get('Ollama', False):
                            alternative_msg += "• ✅ Ollama (local) appears accessible - consider switching to Ollama provider\n"
                        else:
                            alternative_msg += "• ❌ Ollama (local) not running - install and run Ollama for offline processing\n"
                        
                        result['error'] += alternative_msg
                        
                elif provider == "Ollama":
                    self._log_debug("_convert_with_ai: Calling Ollama API")
                    success, result = self._call_ollama(prompt, model)
                else:
                    error_msg = f"Unsupported AI provider: {provider}"
                    self._log_debug(f"_convert_with_ai: {error_msg}")
                    return False, {"error": error_msg}
                
                self._log_debug(f"_convert_with_ai: API call completed, success={success}")
                
                if success:
                    # Log the response - AVOID pandas.Timestamp
                    response_timestamp = datetime.datetime.now().isoformat()
                    
                    self.response_log.append({
                        "response_length": len(result.get('yaml_content', '')),
                        "provider": provider,
                        "timestamp": response_timestamp
                    })
                    
                    self._log_debug("_convert_with_ai: Response logged successfully")
                
                return success, result
                
            except Exception as api_error:
                error_msg = f"API call failed: {str(api_error)}"
                self._log_debug(f"_convert_with_ai: {error_msg}")
                return False, {"error": error_msg}
                
        except Exception as overall_error:
            error_msg = f"AI conversion failed: {str(overall_error)}"
            self._log_debug(f"_convert_with_ai: {error_msg}")
            return False, {"error": error_msg}
    
    def _call_openai(self, prompt: str, api_key: str, model: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Call OpenAI API for YAML conversion."""
        if model is None:
            model = self.model
            
        try:
            import openai
            
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4000,
                temperature=0.1
            )
            
            yaml_content = response.choices[0].message.content.strip()
            
            # Clean the response (remove markdown formatting if present)
            yaml_content = self._clean_yaml_response(yaml_content)
            
            return True, {
                'yaml_content': yaml_content.strip(),
                'model': model,
                'provider': 'OpenAI'
            }
            
        except Exception as e:
            return False, {"error": f"OpenAI API call failed: {str(e)}"}
    
    def _call_govtech(self, prompt: str, api_key: str, model: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Call GovTech API for YAML conversion with enhanced error handling."""
        if model is None:
            model = self.model
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # Configure session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': model,
                'messages': [{"role": "user", "content": prompt}],
                'max_tokens': 4000,
                'temperature': 0.1
            }
            
            # Add timeout and improved error handling
            response = session.post(
                'https://llmaas.govtext.gov.sg/gateway/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                yaml_content = result['choices'][0]['message']['content'].strip()
                
                # Clean the response
                yaml_content = self._clean_yaml_response(yaml_content)
                
                return True, {
                    'yaml_content': yaml_content.strip(),
                    'model': model,
                    'provider': 'GovTech'
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return False, {"error": f"GovTech API error: {error_msg}"}
                
        except requests.exceptions.ConnectionError as e:
            error_msg = ("GovTech API connection failed. This could be due to:\n"
                        "• Network connectivity issues\n"
                        "• Firewall blocking the connection\n"
                        "• DNS resolution problems\n"
                        "• GovTech API endpoint temporarily unavailable\n"
                        f"Details: {str(e)}")
            return False, {"error": error_msg}
        except requests.exceptions.Timeout:
            return False, {"error": "GovTech API request timed out (30s). Try again later."}
        except requests.exceptions.RequestException as e:
            return False, {"error": f"GovTech API request failed: {str(e)}"}
        except Exception as e:
            return False, {"error": f"GovTech API call failed: {str(e)}"}
    
    def _call_ollama(self, prompt: str, model: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Call Ollama API for YAML conversion."""
        if model is None:
            model = self.model
        try:
            import requests
            import json
            
            # Ollama API endpoint (default local installation)
            ollama_url = "http://localhost:11434/api/generate"
            
            payload = {
                'model': model,  # e.g., 'llama3.2:latest'
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,
                    'num_predict': 4000
                }
            }
            
            response = requests.post(ollama_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                yaml_content = result.get('response', '').strip()
                
                # Clean the response (remove markdown formatting if present)
                yaml_content = self._clean_yaml_response(yaml_content)
                
                return True, {
                    'yaml_content': yaml_content.strip(),
                    'model': model,
                    'provider': 'Ollama'
                }
            else:
                return False, {"error": f"Ollama API error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return False, {"error": "Could not connect to Ollama. Make sure Ollama is running on localhost:11434"}
        except requests.exceptions.Timeout:
            return False, {"error": "Ollama request timed out. The model might be processing a large request."}
        except Exception as e:
            return False, {"error": f"Ollama API call failed: {str(e)}"}
    
    def get_logs(self) -> Dict[str, List]:
        """Get prompt and response logs for debugging."""
        return {
            'prompt_log': self.prompt_log,
            'response_log': self.response_log
        }
    
    def _validate_jsonlogic_rules(self, yaml_content: str) -> Dict[str, Any]:
        """Validate JsonLogic rules in the generated YAML."""
        try:
            yaml_data = yaml.safe_load(yaml_content)
            validation_results = {
                'has_jsonlogic': False,
                'valid_rules': 0,
                'invalid_rules': 0,
                'errors': []
            }
            
            # Check each clause in the YAML
            for clause_key, clause_data in yaml_data.items():
                if isinstance(clause_data, dict) and 'jsonlogic_rules' in clause_data:
                    validation_results['has_jsonlogic'] = True
                    rules = clause_data['jsonlogic_rules']
                    
                    # Handle list format (structured rules)
                    if isinstance(rules, list):
                        for rule in rules:
                            if isinstance(rule, dict) and 'rule' in rule:
                                rule_name = rule.get('name', 'Unknown')
                                rule_logic = rule['rule']
                                self._validate_single_jsonlogic_rule(
                                    rule_name, rule_logic, validation_results
                                )
                    
                    # Handle dictionary format (rule_name: rule_logic)
                    elif isinstance(rules, dict):
                        for rule_name, rule_logic in rules.items():
                            self._validate_single_jsonlogic_rule(
                                rule_name, rule_logic, validation_results
                            )
            
            return validation_results
        except Exception as e:
            return {
                'has_jsonlogic': False,
                'valid_rules': 0,
                'invalid_rules': 0,
                'errors': [f"Validation failed: {str(e)}"]
            }
    
    def _validate_single_jsonlogic_rule(self, rule_name: str, rule_logic: Any, 
                                       validation_results: Dict[str, Any]) -> None:
        """Validate a single JsonLogic rule with enhanced error handling."""
        try:
            # First, check if rule_logic is a valid structure
            if not isinstance(rule_logic, dict):
                raise ValueError(f"Rule logic must be a dictionary, got {type(rule_logic)}")
            
            # Check for empty rule
            if not rule_logic:
                raise ValueError("Rule logic is empty")
            
            # Convert any dict_keys objects to lists within the rule
            cleaned_rule = self._clean_jsonlogic_structure(rule_logic)
            
            # Double-check for any remaining dict_keys by doing a deep serialize/deserialize
            try:
                import json
                # Serialize to JSON and back to ensure no dict_keys remain
                json_str = json.dumps(cleaned_rule)
                cleaned_rule = json.loads(json_str)
            except Exception:
                # If serialization fails, stick with the cleaned version
                pass
            
            # Debug logging to see what we're actually validating
            # self._log_debug(f"Validating rule '{rule_name}', cleaned type: {type(cleaned_rule)}")
            
            # Test JsonLogic rule validity with comprehensive test data
            test_data = {
                "test_param": 100,
                "gfa_m2": 50,
                "hs_area": 1.5,
                "hs_area_clear_ge_1500_mm_m2": 1.5,
                "hs_enclosed_volume_m3": 4.0,
                "hs_ceiling_slab_thickness_mm": 300,
                "staircase_waist_thickness_mm": 300,
                "vent_sleeve_wall_clearance_mm": 700,
                "floor_area": 1.5,
                "volume": 4.0,
                "height": 2.4,
                "clearance": 0.6,
                "thickness": 0.15
            }
            
            # Attempt to run the JsonLogic rule (test for validity)
            json_logic.jsonLogic(cleaned_rule, test_data)
            validation_results['valid_rules'] += 1
            
        except Exception as e:
            validation_results['invalid_rules'] += 1
            # Provide more detailed error information
            error_msg = str(e)
            
            # Debug logging for the actual error
            # self._log_debug(f"Rule '{rule_name}' validation failed: {error_msg}")
            
            # Check for specific error types without false positives
            error_lower = error_msg.lower()
            if "dict_keys" in error_lower:
                error_msg = "Rule contains dict_keys object - structure needs cleaning"
            elif "object is not subscriptable" in error_lower:
                error_msg = "Rule structure contains non-subscriptable objects"
            elif "not supported between instances" in error_lower:
                error_msg = "Rule contains incompatible data types for comparison"
            elif "jsonlogic" in error_lower and "error" in error_lower:
                error_msg = f"JsonLogic execution error: {error_msg}"
            
            validation_results['errors'].append({
                'rule': rule_name,
                'error': error_msg,
                'rule_preview': str(rule_logic)[:200] + "..." if len(str(rule_logic)) > 200 else str(rule_logic)
            })
    
    def _clean_jsonlogic_structure(self, obj: Any) -> Any:
        """Recursively clean JsonLogic structures to avoid dict_keys issues."""
        import json
        
        if obj is None:
            return obj
        
        # Convert obj to string and check for problematic types
        obj_str = str(type(obj))
        
        # Handle dict_keys objects specifically
        if 'dict_keys' in obj_str:
            return list(obj)
        
        # Handle dict_values objects
        if 'dict_values' in obj_str:
            return list(obj)
        
        # Handle dict_items objects
        if 'dict_items' in obj_str:
            return dict(obj)
        
        # Handle KeysView, ValuesView, ItemsView from collections.abc
        if hasattr(obj, '__iter__') and ('KeysView' in obj_str or 'ValuesView' in obj_str):
            return list(obj)
        
        if isinstance(obj, dict):
            # Create new dict with cleaned values
            cleaned = {}
            for key, value in obj.items():
                # Ensure keys are strings and values are cleaned
                clean_key = str(key) if not isinstance(key, (str, int, float)) else key
                cleaned[clean_key] = self._clean_jsonlogic_structure(value)
            return cleaned
        elif isinstance(obj, list):
            # Clean all list items
            cleaned_list = []
            for item in obj:
                cleaned_list.append(self._clean_jsonlogic_structure(item))
            return cleaned_list
        elif isinstance(obj, tuple):
            # Convert tuples to lists and clean
            return [self._clean_jsonlogic_structure(item) for item in obj]
        elif hasattr(obj, 'keys') and not isinstance(obj, dict):
            # Handle dict-like objects that aren't actual dicts
            try:
                if hasattr(obj, 'items'):
                    # Convert to proper dict
                    return {str(k): self._clean_jsonlogic_structure(v) for k, v in obj.items()}
                else:
                    # Convert keys to list
                    return list(obj)
            except Exception:
                return str(obj)
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, dict)):
            # Handle other iterable objects (but not strings or bytes)
            try:
                return [self._clean_jsonlogic_structure(item) for item in obj]
            except Exception:
                return str(obj)
        else:
            # Return primitive values as-is, but ensure they're JSON-serializable
            try:
                json.dumps(obj)  # Test if it's JSON serializable
                return obj
            except (TypeError, ValueError):
                # Convert non-serializable objects to string
                return str(obj)
    
    def _extract_jsonlogic_rules(self, yaml_content: str) -> Optional[Dict[str, Any]]:
        """Extract JsonLogic rules from YAML for separate download."""
        try:
            yaml_data = yaml.safe_load(yaml_content)
            extracted_rules = {}
            
            for clause_key, clause_data in yaml_data.items():
                if isinstance(clause_data, dict) and 'jsonlogic_rules' in clause_data:
                    rules = clause_data['jsonlogic_rules']
                    if isinstance(rules, list) and rules:
                        extracted_rules[clause_key] = {
                            'description': clause_data.get('description', ''),
                            'reference': clause_data.get('references', {}),
                            'rules': rules
                        }
            
            return extracted_rules if extracted_rules else None
        except Exception:
            return None
    
    def _clean_yaml_placeholders(self, yaml_content: str) -> str:
        """Clean any remaining template placeholders that might cause parsing issues."""
        try:
            # Remove common problematic placeholder patterns
            import re
            
            # Remove brackets around placeholder text that might be literal
            yaml_content = re.sub(r'\[([a-zA-Z_][a-zA-Z0-9_]*)\]', r'\1', yaml_content)
            
            # Fix common category placeholder issues
            yaml_content = re.sub(r'category: \[.*?\]', 'category: "length"', yaml_content)
            yaml_content = re.sub(r'unit: "\[.*?\]"', 'unit: "mm"', yaml_content)
            yaml_content = re.sub(r'to_canonical: \[.*?\]', 'to_canonical: 1.0', yaml_content)
            
            # Clean any remaining problematic patterns
            yaml_content = re.sub(r': \[.*?\](?=\s*$)', ': null', yaml_content, flags=re.MULTILINE)
            
            return yaml_content
        except Exception:
            # If cleaning fails, return original content
            return yaml_content
    
    def _clean_yaml_jsonlogic_rules(self, yaml_content: str) -> str:
        """Clean JsonLogic rules in YAML content to prevent dict_keys issues."""
        try:
            # Parse YAML to clean the structure
            yaml_data = yaml.safe_load(yaml_content)
            
            # Process each clause to clean JsonLogic rules
            for clause_key, clause_data in yaml_data.items():
                if isinstance(clause_data, dict) and 'jsonlogic_rules' in clause_data:
                    rules = clause_data['jsonlogic_rules']
                    
                    # Clean the JsonLogic rules structure
                    cleaned_rules = self._clean_jsonlogic_structure(rules)
                    clause_data['jsonlogic_rules'] = cleaned_rules
            
            # Convert back to YAML with clean formatting
            cleaned_yaml = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True,
                                   indent=2, width=120, sort_keys=False)
            return cleaned_yaml
            
        except Exception:
            # self._log_debug(f"Error cleaning JsonLogic rules: {e}")
            # If cleaning fails, return original content
            return yaml_content
    
    def render_step1_ui(self):
        """Render Step 1 UI components for unified document processing."""
        try:
            import streamlit as st
            
            st.subheader("Step 1: Document Processing & Parameter Generation")
            st.write("Upload CSV, TXT, or XLS files to convert them into structured YAML and JSON with JsonLogic rules.")
            
            # Check if we have persistent results from previous processing
            if 'step1_results' in st.session_state and st.session_state.step1_results:
                st.success("✅ Previously processed files are available for download!")
                
                # Display persistent download section
                with st.expander("📥 Download Previously Generated Files", expanded=True):
                    prev_results = st.session_state.step1_results
                    uploaded_filename = prev_results.get('uploaded_filename', 'processed_file')
                    base_filename = uploaded_filename.rsplit('.', 1)[0] if '.' in uploaded_filename else uploaded_filename
                    processed_at = prev_results.get('processed_at', 'Unknown')
                    
                    st.info(f"Files processed at: {processed_at}")
                    st.info(f"Source file: {uploaded_filename}")
                    
                    # Prepare download data
                    yaml_data = prev_results.get('yaml_content', '')
                    json_result = prev_results.get('json_result', {})
                    json_data = ""
                    jsonlogic_data = ""
                    
                    if json_result.get('success'):
                        json_data = json.dumps(json_result['json_content'], indent=2)
                        if json_result.get('jsonlogic_rules'):
                            jsonlogic_data = json.dumps(json_result['jsonlogic_rules'], indent=2)
                    
                    # Create ZIP file function for persistent downloads
                    def create_persistent_zip():
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Add YAML file
                            if yaml_data:
                                zip_file.writestr(f"{base_filename}.yaml", yaml_data)
                            
                            # Add JSON parameters if available
                            if json_data:
                                zip_file.writestr(f"{base_filename}_parameters.json", json_data)
                            
                            # Add JsonLogic rules if available
                            if jsonlogic_data:
                                zip_file.writestr(f"{base_filename}_jsonlogic.json", jsonlogic_data)
                            
                            # Add README
                            readme_content = f"""AEC Compliance Analysis - Generated Files
=====================================
Generated on: {processed_at}
Source file: {uploaded_filename}

Files included:
- {base_filename}.yaml: Structured YAML specification
- {base_filename}_parameters.json: Machine-readable JSON parameters
- {base_filename}_jsonlogic.json: JsonLogic validation rules

Download these files persists across page refreshes until a new file is processed.
"""
                            zip_file.writestr("README.txt", readme_content)
                        
                        zip_buffer.seek(0)
                        return zip_buffer.getvalue()
                    
                    # Persistent download buttons with unique keys
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    # Use session-based unique keys for persistent downloads
                    persist_key = prev_results.get('session_key', 'default')
                    
                    with col1:
                        if yaml_data:
                            st.download_button(
                                label="📄 YAML",
                                data=yaml_data,
                                file_name=f"{base_filename}.yaml",
                                mime="application/x-yaml",
                                key=f"persist_yaml_{persist_key}",
                                use_container_width=True
                            )
                    
                    with col2:
                        if json_data:
                            st.download_button(
                                label="🏗️ JSON Params",
                                data=json_data,
                                file_name=f"{base_filename}_parameters.json",
                                mime="application/json",
                                key=f"persist_json_{persist_key}",
                                use_container_width=True
                            )
                    
                    with col3:
                        if jsonlogic_data:
                            st.download_button(
                                label="⚡ JsonLogic",
                                data=jsonlogic_data,
                                file_name=f"{base_filename}_jsonlogic.json",
                                mime="application/json",
                                key=f"persist_jsonlogic_{persist_key}",
                                use_container_width=True
                            )
                    
                    with col4:
                        st.download_button(
                            label="📦 All Files (ZIP)",
                            data=create_persistent_zip(),
                            file_name=f"{base_filename}_complete.zip",
                            mime="application/zip",
                            key=f"persist_zip_{persist_key}",
                            use_container_width=True
                        )
                    
                    with col5:
                        # Clear persistent results
                        if st.button("🗑️ Clear", use_container_width=True, help="Clear saved files to process new document", key=f"clear_{persist_key}"):
                            if 'step1_results' in st.session_state:
                                del st.session_state.step1_results
                            st.rerun()
                
                st.markdown("---")
                st.write("**Process a new document:**")
            
            # Show API key status for debugging
            with st.expander("🔧 API Configuration Status"):
                username = st.session_state.get('username', 'guest')
                provider = st.session_state.get('ai_provider', 'OpenAI')
                
                try:
                    from agents.core.api_key_manager import api_key_manager
                    has_key = bool(api_key_manager.get_api_key(provider, username))
                    
                    st.success(f"✅ {provider} API key configured for user '{username}'") if has_key else st.warning(f"⚠️ No {provider} API key for user '{username}'")
                    
                    # Show available providers
                    try:
                        available_providers = api_key_manager.get_available_providers(username)
                        if available_providers:
                            st.info(f"Available providers: {', '.join(available_providers.keys())}")
                    except:
                        pass
                        
                except Exception as e:
                    st.error(f"API key check failed: {str(e)}")
            
            # File upload
            uploaded_file = st.file_uploader(
                "Choose a document file", 
                type=['csv', 'txt', 'xls', 'xlsx'],
                key="step0_file_upload"
            )
            
            if uploaded_file is not None:
                st.success(f"File uploaded: {uploaded_file.name}")
                
                # Custom prompt options
                with st.expander("Advanced: Custom Prompts (Optional)"):
                    st.write("Use custom prompts for specialized clause parsing needs:")
                    
                    custom_prompt_type = st.radio(
                        "Prompt Type",
                        ["Default (Recommended)", "Custom Combined", "Custom User Only"],
                        key="custom_prompt_type"
                    )
                    
                    if custom_prompt_type == "Custom Combined":
                        custom_combined = st.text_area(
                            "Custom Combined Prompt",
                            height=200,
                            placeholder="Enter your complete custom prompt with {document_content} placeholder...",
                            key="custom_combined_prompt"
                        )
                        if custom_combined.strip():
                            self.set_custom_prompts(combined_prompt=custom_combined)
                    
                    elif custom_prompt_type == "Custom User Only":
                        custom_user = st.text_area(
                            "Custom User Prompt",
                            height=150,
                            placeholder="Enter your user prompt with {document_content} placeholder...",
                            key="custom_user_prompt"
                        )
                        if custom_user.strip():
                            self.set_custom_prompts(user_prompt=custom_user)
                
                # Process button
                if st.button("Convert to YAML and JSON with JsonLogic", key="convert_to_yaml", type="primary"):
                    # Get API key from global manager with current user context
                    api_key = None
                    
                    try:
                        # Get current user and provider from session state
                        username = st.session_state.get('username', 'guest')
                        provider = st.session_state.get('ai_provider', 'OpenAI')
                        
                        # Import the global API key manager
                        from agents.core.api_key_manager import api_key_manager
                        api_key = api_key_manager.get_api_key(provider, username)
                        
                    except Exception as e:
                        st.error(f"Could not get API key: {str(e)}")
                        
                        # Provide helpful guidance based on user type and provider
                        username = st.session_state.get('username', 'guest')
                        provider = st.session_state.get('ai_provider', 'OpenAI')
                        is_admin = username == 'admin'
                        
                        if is_admin:
                            st.info(f"� **Admin Setup Required**\n\n"
                                   f"1. Configure {provider} API key in the sidebar settings\n"
                                   f"2. Or use BYOK (Bring Your Own Key) option below")
                        else:
                            st.info(f"🔑 **API Key Required**\n\n"
                                   f"1. Select '{provider}' provider in the sidebar\n"
                                   f"2. Enter your API key in the BYOK section\n"
                                   f"3. Or ask your admin to configure system keys")
                        
                        return
                    
                    if not api_key:
                        # Special case: Ollama doesn't require an API key (local deployment)
                        if provider == "Ollama":
                            api_key = None  # Explicitly set to None for Ollama
                            st.info(f"🦙 **Ollama Configuration**\n"
                                   f"- Provider: {provider}\n"
                                   f"- Status: Local deployment (no API key required)\n"
                                   f"- Endpoint: http://localhost:11434")
                        else:
                            st.error("❌ No API key available for the selected provider.")
                            
                            # Show current configuration status for other providers
                            username = st.session_state.get('username', 'guest')
                            provider = st.session_state.get('ai_provider', 'OpenAI')
                            
                            st.info(f"**Current Configuration:**\n"
                                   f"- User: {username}\n" 
                                   f"- Provider: {provider}\n"
                                   f"- Status: No API key configured")
                            
                            return
                    
                    # Process the file
                    with st.spinner("Converting document to YAML..."):
                        success, result = self.parse_document_to_yaml(
                            uploaded_file.getvalue(),
                            uploaded_file.name,
                            api_key
                        )
                    
                    if success:
                        st.success("✅ Document successfully converted to YAML!")
                        
                        # Also generate JSON parameters immediately for download
                        json_generator = JsonParameterGenerator()
                        
                        with st.spinner("Generating JSON parameters..."):
                            json_result = json_generator.generate_json_from_yaml(
                                result['yaml_content'], 
                                result['filename']
                            )
                        
                        # Store both YAML and JSON results in session state for persistent downloads
                        # Use a unique key based on filename and timestamp to avoid conflicts
                        session_key = f"step1_results_{uploaded_file.name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                        
                        if 'step1_results' not in st.session_state:
                            st.session_state.step1_results = {}
                        
                        st.session_state.step1_results = {
                            'yaml_content': result['yaml_content'],
                            'filename': result['filename'],
                            'document_preview': result.get('document_preview', ''),
                            'conversion_method': result.get('conversion_method', 'AI'),
                            'json_result': json_result,  # Store JSON results too
                            'processed_at': pd.Timestamp.now().isoformat(),
                            'uploaded_filename': uploaded_file.name,  # Store original filename
                            'session_key': session_key,  # Store session key for unique identification
                            'download_ready': True  # Flag to indicate downloads are ready
                        }
                        
                        # Also store in a separate key to prevent overwrites during rerun
                        st.session_state[session_key] = st.session_state.step1_results.copy()
                        
                        # Show JsonLogic validation results
                        jsonlogic_results = result.get('jsonlogic_validated', {})
                        if jsonlogic_results.get('has_jsonlogic'):
                            valid_count = jsonlogic_results.get('valid_rules', 0)
                            invalid_count = jsonlogic_results.get('invalid_rules', 0)
                            
                            if invalid_count == 0:
                                st.success(f"✅ JsonLogic: {valid_count} valid rules generated")
                            else:
                                st.warning(f"⚠️ JsonLogic: {valid_count} valid, {invalid_count} invalid rules")
                                
                                with st.expander("JsonLogic Validation Errors"):
                                    for error in jsonlogic_results.get('errors', []):
                                        st.error(f"Rule '{error['rule']}': {error['error']}")
                        else:
                            st.info("ℹ️ No JsonLogic rules generated in this conversion")
                        
                        # JSON generation status
                        if json_result['success']:
                            json_content = json_result['json_content']
                            param_count = len(json_content.get('parameters', {}).get('parameter_templates', {}))
                            rule_count = len(json_content.get('jsonlogic_rules', []))
                            st.success(f"✅ JSON parameters generated: {param_count} parameters, {rule_count} JsonLogic rules")
                        
                        # Display results
                        if json_result['success']:
                            # Three columns: Document, YAML, JSON
                            col1, col2, col3 = st.columns([1, 1, 1])
                            
                            with col1:
                                st.write("**Document Preview:**")
                                document_content = result.get('document_preview', '')
                                st.caption(f"📄 Full document content ({len(document_content):,} characters)")
                                
                                # Use expandable code block for better readability without scrolling
                                with st.expander("📖 View Full Document Content", expanded=False):
                                    st.code(document_content, language="text", line_numbers=False)
                            
                            with col2:
                                st.write("**Generated YAML:**")
                                with st.expander("📄 View Generated YAML", expanded=False):
                                    st.code(result['yaml_content'], language='yaml', line_numbers=True)
                            
                            with col3:
                                st.write("**Generated JSON:**")
                                json_display = json.dumps(json_result['json_content'], indent=2)
                                
                                # Show JSON structure info
                                json_content = json_result['json_content']
                                param_count = len(json_content.get('parameters', {}).get('parameter_templates', {}))
                                rule_count = len(json_content.get('jsonlogic_rules', []))
                                st.caption(f"📊 {param_count} parameters, {rule_count} JsonLogic rules")
                                
                                with st.expander("📄 View Generated JSON", expanded=False):
                                    st.code(json_display, language='json', line_numbers=True)
                        
                        else:
                            # Two columns if JSON generation failed: Document, YAML only
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.write("**Document Preview:**")
                                document_content = result.get('document_preview', '')
                                st.caption(f"📄 Full document content ({len(document_content):,} characters)")
                                
                                # Use expandable code block for better readability without scrolling
                                with st.expander("📖 View Full Document Content", expanded=False):
                                    st.code(document_content, language="text", line_numbers=False)
                            
                            with col2:
                                st.write("**Generated YAML:**")
                                with st.expander("📄 View Generated YAML", expanded=False):
                                    st.code(result['yaml_content'], language='yaml', line_numbers=True)
                        
                        # Download options - Enhanced with JSON parameters and ZIP option
                        st.markdown("### 📥 Download Generated Files")
                        
                        # Create download data for persistence
                        yaml_filename = uploaded_file.name.rsplit('.', 1)[0] + '.yaml'
                        base_filename = uploaded_file.name.rsplit('.', 1)[0]
                        
                        # Prepare all download data
                        yaml_data = result['yaml_content']
                        json_data = ""
                        jsonlogic_data = ""
                        
                        if json_result['success']:
                            json_data = json.dumps(json_result['json_content'], indent=2)
                            if json_result['jsonlogic_rules']:
                                jsonlogic_data = json.dumps(json_result['jsonlogic_rules'], indent=2)
                        
                        # Create ZIP file for all downloads
                        def create_zip_file():
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                # Add YAML file
                                zip_file.writestr(f"{base_filename}.yaml", yaml_data)
                                
                                # Add JSON parameters if available
                                if json_data:
                                    zip_file.writestr(f"{base_filename}_parameters.json", json_data)
                                
                                # Add JsonLogic rules if available
                                if jsonlogic_data:
                                    zip_file.writestr(f"{base_filename}_jsonlogic.json", jsonlogic_data)
                                
                                # Add README with file descriptions
                                readme_content = f"""AEC Compliance Analysis - Generated Files
=====================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source file: {uploaded_file.name}

Files included:
- {base_filename}.yaml: Structured YAML specification with clause definitions
- {base_filename}_parameters.json: Machine-readable JSON with comprehensive parameters
- {base_filename}_jsonlogic.json: JsonLogic rules for automated validation

For more information, visit the AEC Compliance Analysis documentation.
"""
                                zip_file.writestr("README.txt", readme_content)
                            
                            zip_buffer.seek(0)
                            return zip_buffer.getvalue()
                        
                        # Create four columns for download options with unique keys
                        col1, col2, col3, col4 = st.columns(4)
                        
                        # Use timestamp-based unique keys to prevent conflicts
                        timestamp = pd.Timestamp.now().strftime('%H%M%S')
                        
                        with col1:
                            st.download_button(
                                label="📄 Download YAML",
                                data=yaml_data,
                                file_name=yaml_filename,
                                mime="application/x-yaml",
                                key=f"yaml_{timestamp}",
                                use_container_width=True,
                                help="Download the structured YAML specification"
                            )
                        
                        with col2:
                            # Download structured JSON parameters
                            if json_result['success'] and json_data:
                                json_filename = f"{base_filename}_parameters.json"
                                st.download_button(
                                    label="🏗️ JSON Parameters",
                                    data=json_data,
                                    file_name=json_filename,
                                    mime="application/json",
                                    key=f"json_{timestamp}",
                                    use_container_width=True,
                                    help="Download structured JSON with parameters and metadata"
                                )
                            else:
                                st.button(
                                    "🏗️ JSON Parameters", 
                                    disabled=True, 
                                    use_container_width=True,
                                    help="JSON generation failed",
                                    key=f"json_disabled_{timestamp}"
                                )
                        
                        with col3:
                            # Download JsonLogic rules separately
                            if json_result['success'] and jsonlogic_data:
                                jsonlogic_filename = f"{base_filename}_jsonlogic.json"
                                st.download_button(
                                    label="⚡ JsonLogic Rules",
                                    data=jsonlogic_data,
                                    file_name=jsonlogic_filename,
                                    mime="application/json",
                                    key=f"jsonlogic_{timestamp}",
                                    use_container_width=True,
                                    help="Download JsonLogic rules for validation"
                                )
                            else:
                                st.button(
                                    "⚡ JsonLogic Rules", 
                                    disabled=True, 
                                    use_container_width=True,
                                    help="No JsonLogic rules generated",
                                    key=f"jsonlogic_disabled_{timestamp}"
                                )
                        
                        with col4:
                            # Download all files as ZIP
                            zip_filename = f"{base_filename}_complete.zip"
                            st.download_button(
                                label="📦 Download All (ZIP)",
                                data=create_zip_file(),
                                file_name=zip_filename,
                                mime="application/zip",
                                key=f"zip_{timestamp}",
                                use_container_width=True,
                                help="Download all generated files in one ZIP archive"
                            )
                        
                        # Show what's included in each download
                        with st.expander("📋 What's included in each download"):
                            st.markdown("""
                            **📄 YAML File**: Original structured YAML specification
                            - Clause definitions and parameters
                            - Tables and compliance rules  
                            - Raw JsonLogic rules (if any)
                            
                            **🏗️ JSON Parameters**: Machine-readable structured data
                            - Comprehensive parameter definitions with metadata
                            - Structured tables with column information
                            - Compliance rules with validation details
                            - Complete JsonLogic rules with variable mapping
                            
                            **⚡ JsonLogic Rules**: Standalone validation rules
                            - Pure JsonLogic rule format for automated validation
                            - Ready for integration with JsonLogic processors
                            - Contains all extracted validation logic
                            """)
                        
                        # Step 1 complete - ready for Step 2
                        st.markdown("---")
                        st.success("✅ Step 1 complete! YAML and JSON files ready. Scroll down to continue with Step 2 (Drawing Analysis).")
                    
                    else:
                        error_message = result.get('error', 'Unknown error')
                        st.error(f"❌ Conversion failed: {error_message}")
                        
                        # Provide specific guidance for connection errors
                        if "GovTech API connection failed" in error_message:
                            with st.expander("🔧 Connection Troubleshooting Guide", expanded=True):
                                st.markdown("""
                                **GovTech API Connection Issues**
                                
                                The application cannot connect to GovTech's AI models. This might be due to:
                                
                                **🔍 Possible Causes:**
                                - Network connectivity issues
                                - Corporate firewall blocking external connections
                                - DNS resolution problems
                                - GovTech API endpoint temporarily unavailable
                                
                                **🛠️ Solutions to try:**
                                1. **Check your internet connection** - Try browsing to https://llmaas.govtext.gov.sg
                                2. **Switch to OpenAI provider** - Go to Settings → AI Provider → Select "OpenAI"
                                3. **Use Ollama (offline)** - Install Ollama locally for offline processing
                                4. **Contact IT/Network Admin** - If using corporate network, request access to llmaas.govtext.gov.sg
                                5. **Try again later** - The service might be temporarily unavailable
                                
                                **🔄 Quick Fix:**
                                Go to the sidebar → **Settings** → **AI Provider** and select a different provider.
                                """)
                        
                        # Debug information (collapsed by default unless connection error)
                        expand_debug = "connection failed" in error_message.lower()
                        with st.expander("Debug Information", expanded=expand_debug):
                            st.json(result)
            
            else:
                st.info("Please upload a document file to begin the conversion process.")
                
                # Show example of supported formats
                with st.expander("Supported File Formats & Examples"):
                    st.write("**Supported Formats:**")
                    st.write("- CSV files (.csv) - Including irregular/mixed format CSV")
                    st.write("- Text files (.txt) - Plain text with clause content")  
                    st.write("- Excel files (.xls, .xlsx) - Spreadsheet format")
                    
                    st.write("**Example Structure:**")
                    st.code('''
2.10 HS BENEATH AN INTERNAL STAIRCASE,
"If a HS is located beneath an internal staircase, the following requirements shall apply.",
"(a) For the purpose of determining the minimum internal floor area...",
"(b) For the purpose of determining the minimum internal volume...",
TABLE 2.2.1(b) MINIMUM INTERNAL HS FLOOR AREA AND VOLUME,
GFA* of a House (m2),HS Floor Area (m2),HS Volume (m3),
GFA < 40,1.44,3.6,
40 < GFA < 45,1.6,3.6,
                    ''', language='csv')
            
            # Show processing logs if available
            if hasattr(self, 'prompt_log') and self.prompt_log:
                with st.expander("Processing Logs (Debug)"):
                    logs = self.get_logs()
                    st.json(logs)
        
        except Exception as e:
            st.error(f"Error in Step 0 UI: {str(e)}")