"""
Combined Agent 3: Executive Report Generator with Insights
Combines functionality of original Agent 3 (Executive Report) and Agent 4 (Insights)
to generate both executive summary and detailed insights from compliance analysis.
"""
import os
import pandas as pd
import requests
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from ..utils.prompt_manager import load_agent_prompts
import numpy as np
from .agent3_compliance_comparison import ComplianceComparisonAgent

class CombinedExecutiveReporter:
    """
    Combined Agent 3 implementation that provides both executive reporting
    and detailed business insights functionality.
    """
    
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        """Initialize the combined executive reporter."""
        self.provider = provider
        self.model = model
        self.prompt_log = []
        self.response_log = []
        
        # Create a compliance comparison agent
        self.compliance_agent = ComplianceComparisonAgent(provider, model)
        
        # Load prompts from files with fallback to default
        try:
            self.prompt = load_agent_prompts("agent3")
        except Exception:
            self.prompt = self._get_default_prompts()
            
        # Additional insights prompts (from Agent 4)
        try:
            self.insights_prompt = load_agent_prompts("agent4")
        except Exception:
            self.insights_prompt = self._get_default_insights_prompts()
    
    def compare_compliance(self, parameters_csv_path: str, analysis_csv_path: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare analysis results against requirements to determine compliance.
        This method delegates to the ComplianceComparisonAgent.
        
        Args:
            parameters_csv_path: Path to CSV file with requirements parameters
            analysis_csv_path: Path to CSV file with analysis results
            selected_api_key: API key for AI provider
            
        Returns:
            Tuple[bool, Dict]: (success, result)
        """
        # Delegate to the compliance comparison agent
        return self.compliance_agent.compare_compliance(
            parameters_csv_path, analysis_csv_path, selected_api_key
        )
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts for executive reporting."""
        return {
            "system": """You are a senior AEC compliance consultant and risk management expert who creates concise executive-level reports for construction and design projects. You have extensive experience in building codes, regulatory compliance, and translating technical compliance data into business insights and actionable recommendations.

Your expertise includes:
- Building code compliance and regulatory requirements
- Risk assessment and impact analysis for construction projects
- Executive communication and stakeholder reporting
- Remediation strategies and implementation planning

Output Requirements:
- Professional executive-level language suitable for C-suite and board presentations
- Concise structure focusing only on key issues and recommendations
- Clear, actionable recommendations with specific next steps
- Brief business impact analysis""",

            "user": """Generate a concise executive compliance report based on the detailed analysis results provided below.

<compliance_data>
{compliance_data}
</compliance_data>

Create a succinct executive report with the following structure:

## EXECUTIVE SUMMARY
- Overall compliance status and key findings (1-2 sentences)
- Critical risk level assessment (HIGH/MEDIUM/LOW)

## COMPLIANCE DASHBOARD
- Total parameters assessed: [X]
- Compliance rate: [X]% ([compliant]/[total assessed])
- Critical non-compliance items: [X]
- Overall risk level: [HIGH/MEDIUM/LOW]

## KEY NON-COMPLIANCE ISSUES
For each non-compliant parameter:
- **Parameter**: [Name] - **Required**: [Value] vs **Found**: [Value]
- **Risk Level**: [HIGH/MEDIUM/LOW]
- **Source**: [Drawing reference]

## TOP RECOMMENDATIONS
1. [Critical action item with deadline]
2. [Design modifications if needed]
3. [Documentation updates required]

## BUSINESS IMPACT
- Timeline Impact: [X] weeks potential delay
- Key Regulatory Concerns: [Brief summary]

**Report Date**: [Date]
**Analysis Method**: AI-Powered Compliance Assessment
**Confidence Level**: [HIGH/MEDIUM/LOW]

---
*This concise report provides strategic compliance guidance. Implementation should be coordinated with qualified professionals.*"""
        }
    
    def _get_default_insights_prompts(self) -> Dict[str, str]:
        """Get default prompts for insights generation."""
        return {
            "system": """You are an expert AEC (Architecture, Engineering, Construction) data analyst specializing in building code compliance. Your task is to extract structured insights from compliance analysis data and format them in a way that can be saved as CSV data.
        
You specialize in identifying patterns, risks, and actionable recommendations based on building code compliance data.""",

            "user": """Analyze the following compliance data and generate structured insights in a format suitable for CSV output. 

<compliance_data>
{compliance_data}
</compliance_data>

For each parameter in the compliance data, provide the following fields:
1. Category - The broad category the parameter belongs to (Structural, Size, Access, Safety, etc.)
2. Parameter - The exact parameter name from the data
3. Observation - A clear statement about what was observed (1 sentence)
4. Impact - The importance/severity (High/Medium/Low)
5. Recommendation - Specific action to take (1 sentence)

Format your response as JSON with the following structure:
{
  "data": [
    {
      "Category": "category_value",
      "Parameter": "parameter_value",
      "Observation": "observation_text",
      "Impact": "impact_level",
      "Recommendation": "recommendation_text"
    },
    ...
  ]
}

Do not include any explanatory text before or after the JSON."""
        }
    
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent (compatibility with app.py)."""
        return cls()._get_default_prompts()
        
    def set_prompts(self, prompts: Dict[str, str]):
        """Set custom prompts for the executive report agent."""
        if "user" in prompts:
            default_prompts = self._get_default_prompts()
            self.prompt = {"system": prompts.get("system", default_prompts["system"]),
                          "user": prompts["user"]}
        else:
            self.prompt = prompts
    
    def set_insights_prompts(self, prompts: Dict[str, str]):
        """Set custom prompts for the insights report."""
        if "user" in prompts:
            default_prompts = self._get_default_insights_prompts()
            self.insights_prompt = {"system": prompts.get("system", default_prompts["system"]),
                                   "user": prompts["user"]}
        else:
            self.insights_prompt = prompts
    
    def analyze_compliance_data(self, comparisons_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze compliance DataFrame to extract key insights for reporting."""
        total = len(comparisons_df)
        
        # Map 'Compliance (Y/N)' column to 'Compliance_Status' if needed
        if 'Compliance (Y/N)' in comparisons_df.columns and 'Compliance_Status' not in comparisons_df.columns:
            # Create a new Compliance_Status column based on 'Compliance (Y/N)'
            comparisons_df['Compliance_Status'] = comparisons_df['Compliance (Y/N)'].map(
                lambda x: 'Compliant' if x == 'Y' else ('Non-Compliant' if x == 'N' else 'Not Found')
            )
        
        # Now we can use Compliance_Status column
        compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
        non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
        not_found = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Not Found'])
        
        # Identify critical issues
        critical_issues = comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant']
        
        # Group by parameter type if available
        type_breakdown = {}
        if 'type' in comparisons_df.columns:
            type_breakdown = comparisons_df['type'].value_counts().to_dict()
        
        # Compliance by reference if available
        reference_breakdown = {}
        if 'reference' in comparisons_df.columns:
            reference_breakdown = comparisons_df.groupby('reference')['Compliance_Status'].value_counts().to_dict()
        
        return {
            'total_parameters': total,
            'compliance_summary': {
                'compliant': compliant,
                'non_compliant': non_compliant,
                'not_found': not_found,
                'compliance_rate': (compliant / total * 100) if total > 0 else 0
            },
            'critical_issues': critical_issues.to_dict('records') if not critical_issues.empty else [],
            'type_breakdown': type_breakdown,
            'reference_breakdown': reference_breakdown,
            'risk_level': self._assess_risk_level(compliant, non_compliant, total)
        }
    
    def _assess_risk_level(self, compliant: int, non_compliant: int, total: int) -> str:
        """Assess overall risk level based on compliance rates."""
        if total == 0:
            return "UNKNOWN"
        
        compliance_rate = compliant / total
        non_compliance_rate = non_compliant / total
        
        if non_compliance_rate > 0.3:  # More than 30% non-compliant
            return "HIGH"
        elif non_compliance_rate > 0.1:  # More than 10% non-compliant
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_report_summary_stats(self, report_content: str, compliance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the executive report."""
        return {
            'report_length': len(report_content),
            'compliance_rate': compliance_analysis['compliance_summary']['compliance_rate'],
            'risk_level': compliance_analysis['risk_level'],
            'critical_issues_count': len(compliance_analysis['critical_issues']),
            'total_parameters': compliance_analysis['total_parameters'],
            'generation_timestamp': datetime.now().isoformat()
        }
    
    def process_compliance_data(self, compliance_data_df: pd.DataFrame, api_key: str) -> Dict[str, Any]:
        """Process compliance data directly from a DataFrame instead of a CSV file.
        
        Args:
            compliance_data_df: DataFrame containing compliance data
            api_key: Required API key for AI provider
            
        Returns:
            Dict with processing results
        """
        result = {
            'data_analysis': None,
            'report_success': False,
            'insights_success': False,
            'report_content': None,
            'insights_content': None,
            'report_summary': None,
            'error': None
        }
        
        try:
            # Analyze compliance data
            result['data_analysis'] = self.analyze_compliance_data(compliance_data_df)
            
            # Generate executive report
            success, report_result = self._generate_with_ai(compliance_data_df, api_key)
            result['report_success'] = success
            
            if success:
                result['report_content'] = report_result.get('report')
                result['report_summary'] = self.get_report_summary_stats(
                    report_result.get('report', ''),
                    result['data_analysis']
                )
                
                # Save executive report to file
                report_path = "output/executive_report.txt"
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_result.get('report'))
                
                # Generate insights report
                insights_success, insights_result = self._generate_insights_from_df(compliance_data_df, api_key)
                result['insights_success'] = insights_success
                
                if insights_success:
                    result['insights_content'] = insights_result.get('insights')
                    
                    # Save insights to CSV
                    insights_path = "output/executive_insights.csv"
                    try:
                        insights_df = pd.DataFrame(insights_result.get('insights_data'))
                        insights_df.to_csv(insights_path, index=False)
                        
                        # Also save to the standard insights.csv location
                        insights_df.to_csv("output/insights.csv", index=False)
                    except Exception as e:
                        result['error'] = f"Failed to save insights CSV: {str(e)}"
                else:
                    result['error'] = insights_result.get('error')
            else:
                result['error'] = report_result.get('error')
                
        except Exception as e:
            result['error'] = f"Processing error: {str(e)}"
            import traceback
            traceback.print_exc()
        
        return result
    
    def process_compliance_report(self, comparisons_csv_path: str, api_key: str) -> Dict[str, Any]:
        """Complete processing: analyze data, generate reports, and prepare results from CSV file."""
        try:
            # Read compliance data from CSV
            if not os.path.exists(comparisons_csv_path):
                return {
                    'report_success': False,
                    'insights_success': False,
                    'error': f"Comparisons file not found: {comparisons_csv_path}"
                }
            
            comparisons_df = pd.read_csv(comparisons_csv_path)
            
            # Process the DataFrame directly
            return self.process_compliance_data(comparisons_df, api_key)
            
        except Exception as e:
            return {
                'report_success': False,
                'insights_success': False,
                'error': f"Processing error: {str(e)}"
            }
    
    def generate_report(self, comparisons_csv_path: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate executive summary report using AI prompt-response approach.
        
        Args:
            comparisons_csv_path: Path to comparisons.csv from Agent 2
            api_key: Required API key for AI provider
            
        Returns:
            Tuple[bool, Dict]: (success, {"report": str, "summary": dict})
        """
        if not api_key:
            return False, {"error": "API key is required for AI prompt-response approach"}
            
        try:
            # Load comparisons data
            if not os.path.exists(comparisons_csv_path):
                return False, {"error": f"Comparisons file not found: {comparisons_csv_path}"}
            
            comparisons_df = pd.read_csv(comparisons_csv_path)
            
            return self._generate_with_ai(comparisons_df, api_key)
            
        except Exception as e:
            return False, {"error": f"Report generation failed: {str(e)}"}
    
    def _generate_with_ai(self, comparisons_df: pd.DataFrame, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Generate comprehensive executive report using enhanced AI prompts."""
        
        try:
            # Map 'Compliance (Y/N)' column to 'Compliance_Status' if needed
            if 'Compliance (Y/N)' in comparisons_df.columns and 'Compliance_Status' not in comparisons_df.columns:
                # Create a new Compliance_Status column based on 'Compliance (Y/N)'
                comparisons_df['Compliance_Status'] = comparisons_df['Compliance (Y/N)'].map(
                    lambda x: 'Compliant' if x == 'Y' else ('Non-Compliant' if x == 'N' else 'Not Found')
                )
            
            # Prepare comprehensive data summary for AI analysis
            total_params = len(comparisons_df)
            compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
            non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
            not_found = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Not Found'])
            not_analyzed = len(comparisons_df[comparisons_df['Compliance_Status'].str.contains('Not Analyzed', na=False)])
            
            # Calculate compliance rate for assessed items only
            assessed_items = total_params - not_analyzed
            compliance_rate = round((compliant / max(assessed_items, 1)) * 100, 1) if assessed_items > 0 else 0
            
            # Get detailed non-compliant analysis
            critical_issues = comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant']
            missing_data = comparisons_df[comparisons_df['Compliance_Status'] == 'Not Found']
            
            # Prepare structured data for AI analysis
            compliance_summary = f"""
COMPLIANCE ANALYSIS OVERVIEW:
- Total Parameters: {total_params}
- Compliant: {compliant}
- Non-Compliant: {non_compliant}  
- Not Found in Drawings: {not_found}
- Not Analyzed (Missing API): {not_analyzed}
- Compliance Rate: {compliance_rate}% (of {assessed_items} assessed items)

CRITICAL NON-COMPLIANCE DETAILS:
"""
            
            if not critical_issues.empty:
                for _, issue in critical_issues.iterrows():
                    # Get appropriate column for minimum/required value
                    min_value = None
                    for col in ['Required', 'Required_Value', 'Min. Rectilinear HS Countable Area', 'Min. Irregular HS Countable Area']:
                        if col in issue and not pd.isna(issue[col]) and issue[col]:
                            min_value = issue[col]
                            break
                    
                    # Get appropriate column for actual/found value
                    actual_value = None
                    for col in ['Actual', 'Found_Value', 'HS Area', 'HS Volume', 'HS Slab Thickness', 'HS underneath Staircase Waist Thickness']:
                        if col in issue and not pd.isna(issue[col]) and issue[col]:
                            actual_value = issue[col]
                            break
                    
                    unit = issue.get('Unit', '')
                    source = issue.get('Source', issue.get('Reference Drawing', 'Not specified'))
                    description = issue.get('Description', issue.get('Notes', issue.get('Clause', 'No description')))
                    
                    compliance_summary += f"""
Parameter: {issue['Parameter']}
Required Value: {min_value if min_value is not None else 'N/A'} {unit}
Found Value: {actual_value if actual_value is not None else 'N/A'} {unit}
Source: {source}
Confidence: {issue.get('Confidence', 'N/A')}
Description: {description}
---"""
            else:
                compliance_summary += "No critical non-compliance issues identified."
                
            compliance_summary += f"""

MISSING DATA ANALYSIS:
"""
            if not missing_data.empty:
                for _, missing in missing_data.iterrows():
                    # Get appropriate column for minimum/required value
                    min_value = None
                    for col in ['Required', 'Required_Value', 'Min. Rectilinear HS Countable Area', 'Min. Irregular HS Countable Area']:
                        if col in missing and not pd.isna(missing[col]) and missing[col]:
                            min_value = missing[col]
                            break
                    
                    unit = missing.get('Unit', '')
                    description = missing.get('Description', missing.get('Notes', missing.get('Clause', 'No description')))
                    
                    compliance_summary += f"""
Parameter: {missing['Parameter']}
Required: {min_value if min_value is not None else 'N/A'} {unit}
Description: {description}
---"""
            else:
                compliance_summary += "All required parameters were found in the drawings."
                
            compliance_summary += f"""

DETAILED COMPLIANCE TABLE:
{comparisons_df.to_string(index=False, max_colwidth=50)}
"""
            
            # Format user prompt with compliance data
            user_prompt = self.prompt["user"].format(compliance_data=compliance_summary)
            
            # Make OpenAI API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.prompt["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,  # Low temperature for consistent professional reports
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            report_content = response.json()["choices"][0]["message"]["content"].strip()
            
            # Map required columns for summary stats
            if not critical_issues.empty:
                # Map columns based on what's available
                req_col = next((col for col in ['Required_Value', 'Required', 'Min. Rectilinear HS Countable Area'] 
                              if col in critical_issues.columns), None)
                actual_col = next((col for col in ['Found_Value', 'Actual', 'HS Area'] 
                                if col in critical_issues.columns), None)
                notes_col = next((col for col in ['Notes', 'Description', 'Parameter'] 
                               if col in critical_issues.columns), None)
                
                critical_issues_data = []
                for _, row in critical_issues.iterrows():
                    issue_data = {
                        'Parameter': row.get('Parameter', 'Unknown Parameter'),
                        'Required': row.get(req_col, 'N/A') if req_col else 'N/A',
                        'Actual': row.get(actual_col, 'N/A') if actual_col else 'N/A',
                        'Notes': row.get(notes_col, 'No description') if notes_col else 'No description'
                    }
                    critical_issues_data.append(issue_data)
            else:
                critical_issues_data = []
            
            # Same for missing data
            if not missing_data.empty:
                req_col = next((col for col in ['Required_Value', 'Required', 'Min. Rectilinear HS Countable Area'] 
                              if col in missing_data.columns), None)
                notes_col = next((col for col in ['Notes', 'Description', 'Parameter'] 
                               if col in missing_data.columns), None)
                
                missing_data_list = []
                for _, row in missing_data.iterrows():
                    missing_item = {
                        'Parameter': row.get('Parameter', 'Unknown Parameter'),
                        'Required': row.get(req_col, 'N/A') if req_col else 'N/A',
                        'Notes': row.get(notes_col, 'No description') if notes_col else 'No description'
                    }
                    missing_data_list.append(missing_item)
            else:
                missing_data_list = []
            
            # Create enhanced summary statistics for dashboard
            summary_stats = {
                "total_parameters": total_params,
                "compliant_count": compliant,
                "non_compliant_count": non_compliant,
                "not_found_count": not_found,
                "not_analyzed_count": not_analyzed,
                "assessed_items": assessed_items,
                "compliance_rate": compliance_rate,
                "risk_level": "HIGH" if non_compliant > 0 else ("MEDIUM" if not_found > 0 else "LOW"),
                "critical_issues": critical_issues_data,
                "missing_data": missing_data_list
            }
            
            return True, {
                "report": report_content,
                "summary": summary_stats,
                "method": "Enhanced AI Executive Analysis",
                "compliance_rate": compliance_rate,
                "risk_assessment": summary_stats["risk_level"]
            }
            
        except Exception as e:
            return False, {"error": f"AI report generation failed: {str(e)}"}

    def _generate_insights_from_df(self, comparisons_df: pd.DataFrame, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate business insights using AI prompt-response approach directly from a DataFrame.
        
        Args:
            comparisons_df: DataFrame containing compliance data
            api_key: Required API key for AI provider
            
        Returns:
            Tuple[bool, Dict]: (success, {"insights": str, "insights_data": list})
        """
        if not api_key:
            return False, {"error": "API key is required for AI insights generation"}
            
        try:
            # Map 'Compliance (Y/N)' column to 'Compliance_Status' if needed
            if 'Compliance (Y/N)' in comparisons_df.columns and 'Compliance_Status' not in comparisons_df.columns:
                # Create a new Compliance_Status column based on 'Compliance (Y/N)'
                comparisons_df['Compliance_Status'] = comparisons_df['Compliance (Y/N)'].map(
                    lambda x: 'Compliant' if x == 'Y' else ('Non-Compliant' if x == 'N' else 'Not Found')
                )
            
            # Calculate summary statistics
            total_params = len(comparisons_df)
            compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
            non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
            not_found = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Not Found'])
            compliance_rate = round((compliant / total_params) * 100, 1) if total_params > 0 else 0
            
            # Prepare data for insights analysis
            compliance_summary = f"""
COMPLIANCE ANALYSIS OVERVIEW:
- Total Parameters: {total_params}
- Compliant: {compliant}
- Non-Compliant: {non_compliant}  
- Not Found in Drawings: {not_found}
- Compliance Rate: {compliance_rate}%

DETAILED COMPLIANCE TABLE:
{comparisons_df.to_string(index=False, max_colwidth=50)}
"""
            
            # Format user prompt with compliance data
            user_prompt = self.insights_prompt["user"].format(compliance_data=compliance_summary)
            
            # Make OpenAI API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.insights_prompt["system"]},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1  # Low temperature for consistent insights
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            insights_content = response.json()["choices"][0]["message"]["content"].strip()
            
            # Parse insights JSON and extract data
            try:
                # Try to extract JSON from the response (handling cases where AI might add extra text)
                import re
                json_match = re.search(r'({.*})', insights_content, re.DOTALL)
                if json_match:
                    insights_json = json.loads(json_match.group(0))
                else:
                    insights_json = json.loads(insights_content)
                
                if "data" in insights_json:
                    insights_data = insights_json["data"]
                else:
                    insights_data = insights_json
                    
                # Return successful result
                return True, {
                    "insights": insights_content,
                    "insights_data": insights_data
                }
                
            except Exception as e:
                return False, {"error": f"Failed to parse insights data: {str(e)}"}
            
        except Exception as e:
            return False, {"error": f"Insights generation failed: {str(e)}"}
    
    def generate_insights(self, comparisons_csv_path: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate business insights using AI prompt-response approach from a CSV file.
        
        Args:
            comparisons_csv_path: Path to comparisons.csv
            api_key: Required API key for AI provider
            
        Returns:
            Tuple[bool, Dict]: (success, {"insights": str, "insights_data": list})
        """
        if not api_key:
            return False, {"error": "API key is required for AI insights generation"}
            
        try:
            # Load comparisons data
            if not os.path.exists(comparisons_csv_path):
                return False, {"error": f"Comparisons file not found: {comparisons_csv_path}"}
            
            comparisons_df = pd.read_csv(comparisons_csv_path)
            
            # Use the DataFrame method
            return self._generate_insights_from_df(comparisons_df, api_key)
            
        except Exception as e:
            return False, {"error": f"Insights generation failed: {str(e)}"}

# For compatibility with older code that might expect ExecutiveReportGenerator
# We create an alias to the new combined class
ExecutiveReportGenerator = CombinedExecutiveReporter