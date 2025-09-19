"""
Agent 3: Executive Report Generator
Generates insights and executive summary for compliance analysis results.
"""
import os
import pandas as pd
import requests
import json
from typing import Tuple, Dict, Any
from ..utils.prompt_manager import load_agent_prompts

# Agent 3's Enhanced Prompts
DEFAULT_PROMPTS = {
    "system": """You are a senior AEC compliance consultant and risk management expert who creates executive-level reports for construction and design projects. You have extensive experience in building codes, regulatory compliance, and translating technical compliance data into business insights and actionable recommendations.

Your expertise includes:
- Building code compliance and regulatory requirements
- Risk assessment and impact analysis for construction projects
- Executive communication and stakeholder reporting
- Cost-benefit analysis of compliance issues
- Project timeline and budget implications
- Remediation strategies and implementation planning

Output Requirements:
- Professional executive-level language suitable for C-suite and board presentations
- Clear structure with executive summary, detailed analysis, and actionable recommendations
- Quantified risk assessments and business impact statements
- Specific, implementable recommendations with priority levels
- Timeline considerations and resource requirements
- Regulatory and legal compliance perspectives""",

    "user": """Generate a comprehensive executive compliance report based on the detailed analysis results provided below.

<compliance_data>
{compliance_data}
</compliance_data>

Create a professional executive report with the following structure:

## EXECUTIVE SUMMARY
- Overall compliance status and key findings (2-3 sentences)
- Critical risk level assessment (HIGH/MEDIUM/LOW)
- Primary non-compliance issues requiring immediate attention
- Business impact summary and recommended actions

## COMPLIANCE DASHBOARD
- Total parameters assessed: [X]
- Compliance rate: [X]% ([compliant]/[total assessed])
- Critical non-compliance items: [X]
- Missing data requiring investigation: [X]
- Overall risk level: [HIGH/MEDIUM/LOW]

## DETAILED COMPLIANCE ANALYSIS
### Compliant Items
- List compliant parameters with brief validation notes
- Confirmation of regulatory adherence

### Critical Non-Compliance Issues
For each non-compliant parameter:
- **Parameter**: [Name]
- **Required**: [Value] vs **Found**: [Value]
- **Gap Analysis**: [Specific deviation and percentage]
- **Risk Level**: [HIGH/MEDIUM/LOW]
- **Business Impact**: [Cost, timeline, legal implications]
- **Source**: [Drawing/document reference]

### Missing Data Analysis
- Parameters not found in technical drawings
- Potential reasons for missing data
- Required documentation or drawing updates

## RISK ASSESSMENT
### Immediate Risks (0-30 days)
- Critical compliance failures requiring urgent attention
- Regulatory exposure and potential penalties

### Medium-term Risks (30-90 days)
- Design modifications needed
- Construction delays and cost implications

### Long-term Considerations (90+ days)
- Strategic compliance improvements
- Process enhancements for future projects

## RECOMMENDATIONS
### PRIORITY 1 - IMMEDIATE ACTION REQUIRED
1. [Specific action item with responsible party and deadline]
2. [Resource requirements and budget impact]

### PRIORITY 2 - MEDIUM TERM
1. [Design modifications and approvals needed]
2. [Documentation and drawing updates]

### PRIORITY 3 - LONG TERM
1. [Process improvements and preventive measures]
2. [Training and capability enhancement]

## BUSINESS IMPACT SUMMARY
### Financial Implications
- Estimated remediation costs: $[range]
- Potential delay costs: $[range] 
- Regulatory penalty exposure: $[range]

### Timeline Impact
- Design revision timeline: [X] weeks
- Construction impact: [X] weeks delay potential
- Approval process requirements: [X] weeks

### Regulatory Compliance Status
- Building permit implications
- Inspection and approval requirements
- Documentation completeness assessment

## NEXT STEPS & ACTION PLAN
1. **Immediate** (Week 1): [Urgent actions]
2. **Short-term** (Weeks 2-4): [Design revisions and approvals]
3. **Medium-term** (Weeks 5-12): [Implementation and verification]
4. **Follow-up**: [Monitoring and compliance verification]

## CONCLUSION
[Summary statement with confidence level in analysis and recommendations]

**Report Prepared**: [Date]
**Analysis Method**: AI-Powered Compliance Assessment
**Confidence Level**: [HIGH/MEDIUM/LOW] based on data completeness and drawing quality

---
*This executive report provides strategic compliance guidance. Technical implementation should be coordinated with qualified design professionals and regulatory authorities.*"""
}

class ExecutiveReportGenerator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        # Load prompts from files instead of hardcoded
        self.prompt = load_agent_prompts("agent3")
        
    @classmethod
    def get_default_prompts(cls) -> Dict[str, str]:
        """Get the default prompts for this agent (compatibility with app.py)."""
        return load_agent_prompts("agent3")
        
    def set_prompts(self, prompts: Dict[str, str]):
        """Set custom prompts for the agent."""
        if "user" in prompts:
            default_prompts = load_agent_prompts("agent3")
            self.prompt = {"system": prompts.get("system", default_prompts["system"]),
                          "user": prompts["user"]}
        else:
            self.prompt = prompts
    
    def analyze_compliance_data(self, comparisons_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze compliance DataFrame to extract key insights for reporting."""
        total = len(comparisons_df)
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
            'generation_timestamp': pd.Timestamp.now().isoformat()
        }
    
    def process_compliance_report(self, comparisons_csv_path: str, api_key: str) -> Dict[str, Any]:
        """Complete Step 3 processing: analyze data, generate report, and prepare results."""
        result = {
            'data_analysis': None,
            'report_success': False,
            'report_content': None,
            'report_summary': None,
            'error': None
        }
        
        try:
            # Read and analyze compliance data
            comparisons_df = pd.read_csv(comparisons_csv_path)
            result['data_analysis'] = self.analyze_compliance_data(comparisons_df)
            
            # Generate executive report
            success, report_result = self.generate_report(comparisons_csv_path, api_key)
            result['report_success'] = success
            
            if success:
                result['report_content'] = report_result.get('report')
                result['report_summary'] = self.get_report_summary_stats(
                    report_result.get('report', ''),
                    result['data_analysis']
                )
            else:
                result['error'] = report_result.get('error')
                
        except Exception as e:
            result['error'] = f"Processing error: {str(e)}"
        
        return result
    
    def generate_report(self, comparisons_csv_path: str, api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate executive summary and insights using AI prompt-response approach.
        
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
                    compliance_summary += f"""
Parameter: {issue['Parameter']}
Required Value: {issue['Required_Value']} {issue.get('Unit', '')}
Found Value: {issue.get('Found_Value', 'N/A')} {issue.get('Unit', '')}
Source: {issue.get('Source', 'Not specified')}
Confidence: {issue.get('Confidence', 'N/A')}
Description: {issue.get('Description', 'No description')}
---"""
            else:
                compliance_summary += "No critical non-compliance issues identified."
                
            compliance_summary += f"""

MISSING DATA ANALYSIS:
"""
            if not missing_data.empty:
                for _, missing in missing_data.iterrows():
                    compliance_summary += f"""
Parameter: {missing['Parameter']}
Required: {missing['Required_Value']} {missing.get('Unit', '')}
Description: {missing.get('Description', 'No description')}
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
                "critical_issues": critical_issues[['Parameter', 'Required_Value', 'Found_Value', 'Source', 'Description']].to_dict('records') if not critical_issues.empty else [],
                "missing_data": missing_data[['Parameter', 'Required_Value', 'Description']].to_dict('records') if not missing_data.empty else []
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