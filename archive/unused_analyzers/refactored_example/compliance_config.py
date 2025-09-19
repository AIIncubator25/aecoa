"""
Compliance Configuration Manager
Handles compliance templates, HS scenarios, and domain-specific patterns.
"""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ComplianceConfigManager:
    """Manages compliance templates and HS scenarios configuration."""
    
    def __init__(self):
        self.compliance_templates = self._load_compliance_templates()
        self.hs_scenarios = self._load_hs_scenarios()
        self.current_domain = 'hs_household_shelter'
        self.current_scenario = None
        
    def _load_compliance_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load compliance-specific templates for different analysis types."""
        return {
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
            }
        }
    
    def _load_hs_scenarios(self) -> Dict[str, Any]:
        """Load HS scenario configurations for different project types."""
        try:
            # Get project root dynamically
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            scenarios_path = project_root / 'configurations' / 'hs_scenarios.yaml'
            
            if scenarios_path.exists():
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
    
    def set_compliance_domain(self, domain: str) -> bool:
        """Set the compliance domain for analysis."""
        if domain in self.compliance_templates:
            self.current_domain = domain
            print(f"[DEBUG] Set compliance domain to: {self.compliance_templates[domain]['name']}")
            return True
        else:
            available_domains = list(self.compliance_templates.keys())
            print(f"[WARNING] Unknown domain '{domain}'. Available domains: {available_domains}")
            return False
    
    def set_hs_scenario(self, scenario_name: str) -> bool:
        """Set the HS scenario for analysis."""
        scenarios = self.hs_scenarios.get('scenarios', {})
        if scenario_name in scenarios:
            self.current_scenario = scenario_name
            print(f"[DEBUG] Set HS scenario to: {scenarios[scenario_name]['name']}")
            return True
        else:
            available_scenarios = list(scenarios.keys())
            default_scenario = self.hs_scenarios.get('default_scenario', 'residential_standard')
            print(f"[WARNING] Unknown scenario '{scenario_name}'. Available: {available_scenarios}")
            self.current_scenario = default_scenario
            return False
    
    def get_domain_patterns(self) -> Dict[str, Any]:
        """Get domain-specific patterns for current domain."""
        return self.compliance_templates.get(self.current_domain, {}).get('domain_patterns', {})
    
    def get_key_columns(self) -> list:
        """Get key columns for current domain."""
        return self.compliance_templates.get(self.current_domain, {}).get('key_columns', [])
    
    def get_available_domains(self) -> list:
        """Get list of available compliance domains."""
        return list(self.compliance_templates.keys())
    
    def get_available_scenarios(self) -> list:
        """Get list of available HS scenarios."""
        return list(self.hs_scenarios.get('scenarios', {}).keys())