#!/usr/bin/env python3
"""
AI-based Executive Report Generator using the OpenAI API
This script analyzes comparison.csv data and generates insights.csv and executive_report.txt
using AI prompt-response approach instead of hardcoded values.
"""
import os
import sys
import pandas as pd
import requests
import json
from datetime import datetime
import dotenv

# Add project root to path to allow importing from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Load environment variables from .env file
dotenv.load_dotenv()

def get_api_key():
    """Get OpenAI API key from environment variables or .streamlit/secrets.toml"""
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try to read from .streamlit/secrets.toml
    if not api_key:
        try:
            # Path to secrets from the project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            secrets_path = os.path.join(project_root, ".streamlit/secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                lines = content.split('\n')
                in_openai_section = False
                for line in lines:
                    line = line.strip()
                    if line == '[openai]':
                        in_openai_section = True
                        continue
                    if in_openai_section and line.startswith('api_key'):
                        api_key = line.split('=')[1].strip().strip('"')
                        break
                    if line.startswith('[') and line != '[openai]':
                        in_openai_section = False
        except Exception as e:
            print(f"Error reading secrets file: {e}")
    
    return api_key

def generate_report_with_ai(comparisons_csv_path, api_key, model="gpt-4o-mini"):
    """Generate executive report and insights using AI"""
    if not api_key:
        print("❌ API key not found. Please set OPENAI_API_KEY environment variable.")
        return False
    
    try:
        # Load comparison data
        if not os.path.exists(comparisons_csv_path):
            print(f"❌ Comparison file not found: {comparisons_csv_path}")
            return False
        
        comparisons_df = pd.read_csv(comparisons_csv_path)
        print(f"✅ Loaded comparison data: {len(comparisons_df)} rows")
        
        # Prepare compliance data for AI analysis
        total_params = len(comparisons_df)
        compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
        non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
        not_found = total_params - compliant - non_compliant
        
        # Calculate compliance rate
        compliance_rate = round((compliant / total_params) * 100, 1) if total_params > 0 else 0
        
        # Format data for AI
        compliance_summary = f"""
COMPLIANCE ANALYSIS OVERVIEW:
- Total Parameters: {total_params}
- Compliant: {compliant}
- Non-Compliant: {non_compliant}
- Not Found or Unclear: {not_found}
- Compliance Rate: {compliance_rate}%

DETAILED COMPLIANCE TABLE:
{comparisons_df.to_string(index=False, max_colwidth=50)}
"""
        
        # System prompt for the executive report
        system_prompt = """You are a senior AEC compliance consultant and risk management expert who creates executive-level reports for construction and design projects. You have extensive experience in building codes, regulatory compliance, and translating technical compliance data into business insights and actionable recommendations.

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
- Regulatory and legal compliance perspectives"""

        # User prompt for the executive report
        user_prompt = f"""Generate a comprehensive executive compliance report based on the detailed analysis results provided below.

<compliance_data>
{compliance_summary}
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
- **Risk Level**: [HIGH/MEDIUM/LOW]
- **Business Impact**: [Cost, timeline, legal implications]

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

## RECOMMENDATIONS
### PRIORITY 1 - IMMEDIATE ACTION REQUIRED
1. [Specific action item with responsible party and deadline]
2. [Resource requirements and budget impact]

### PRIORITY 2 - MEDIUM TERM
1. [Design modifications and approvals needed]
2. [Documentation and drawing updates]

## BUSINESS IMPACT SUMMARY
### Financial Implications
- Estimated remediation costs: $[range]
- Potential delay costs: $[range] 
- Regulatory penalty exposure: $[range]

### Timeline Impact
- Design revision timeline: [X] weeks
- Construction impact: [X] weeks delay potential

## NEXT STEPS & ACTION PLAN
1. **Immediate** (Week 1): [Urgent actions]
2. **Short-term** (Weeks 2-4): [Design revisions and approvals]
3. **Medium-term** (Weeks 5-12): [Implementation and verification]

## CONCLUSION
[Summary statement with confidence level in analysis and recommendations]

**Report Prepared**: [Date]
**Analysis Method**: AI-Powered Compliance Assessment
**Confidence Level**: [HIGH/MEDIUM/LOW] based on data completeness and drawing quality"""

        # System prompt for insights data
        insights_system_prompt = """You are an expert AEC (Architecture, Engineering, Construction) data analyst specializing in building code compliance. Your task is to extract structured insights from compliance analysis data and format them in a way that can be saved as CSV data.
        
You specialize in identifying patterns, risks, and actionable recommendations based on building code compliance data."""

        # User prompt for insights data 
        insights_user_prompt = f"""Analyze the following compliance data and generate structured insights in a format suitable for CSV output. 

<compliance_data>
{compliance_summary}
</compliance_data>

For each parameter in the compliance data, provide the following fields:
1. Category - The broad category the parameter belongs to (Structural, Size, Access, Safety, etc.)
2. Parameter - The exact parameter name from the data
3. Observation - A clear statement about what was observed (1 sentence)
4. Impact - The importance/severity (High/Medium/Low)
5. Recommendation - Specific action to take (1 sentence)

Format your response as JSON with the following structure:
{{
  "data": [
    {{
      "Category": "category_value",
      "Parameter": "parameter_value",
      "Observation": "observation_text",
      "Impact": "impact_level",
      "Recommendation": "recommendation_text"
    }},
    ...
  ]
}}

Do not include any explanatory text before or after the JSON."""

        print("\n🤖 Generating AI executive report...")
        
        # Make API call for executive report
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        report_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1  # Low temperature for consistent professional reports
        }
        
        print("📊 Sending executive report request to OpenAI API...")
        response = requests.post(url, headers=headers, json=report_payload, timeout=120)
        response.raise_for_status()
        
        report_content = response.json()["choices"][0]["message"]["content"].strip()
        print("✅ Received executive report from OpenAI API")
        
        # Make API call for insights data
        insights_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": insights_system_prompt},
                {"role": "user", "content": insights_user_prompt}
            ],
            "temperature": 0.1  # Low temperature for consistent data formatting
        }
        
        print("\n📈 Generating insights data...")
        insights_response = requests.post(url, headers=headers, json=insights_payload, timeout=120)
        insights_response.raise_for_status()
        
        insights_content = insights_response.json()["choices"][0]["message"]["content"].strip()
        print("✅ Received insights data from OpenAI API")
        
        # Parse insights JSON and convert to DataFrame
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
                
            insights_df = pd.DataFrame(insights_data)
            print(f"✅ Parsed insights data: {len(insights_df)} rows")
        except Exception as e:
            print(f"❌ Error parsing insights JSON: {e}")
            print("⚠️ Using raw response as insights data")
            
            # Fallback: Create insights manually if JSON parsing fails
            insights_df = pd.DataFrame({
                "Category": ["Error"],
                "Parameter": ["JSON Parsing Error"],
                "Observation": [f"Failed to parse AI response: {str(e)}"],
                "Impact": ["High"],
                "Recommendation": ["Review AI response manually"]
            })
        
        # Save executive report
        os.makedirs("output", exist_ok=True)
        report_path = "output/executive_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ Executive report saved to {report_path}")
        
        # Save insights data
        insights_path = "output/insights.csv"
        insights_df.to_csv(insights_path, index=False)
        print(f"✅ Insights saved to {insights_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating AI report: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to generate AI-powered reports"""
    print("🚀 AI-POWERED EXECUTIVE REPORT GENERATOR")
    print("=" * 50)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ API key not found")
        return
    print("✅ API key loaded")
    
    # Check for comparison.csv
    comparison_path = "output/comparison.csv"
    if not os.path.exists(comparison_path):
        print(f"❌ Comparison file not found: {comparison_path}")
        return
    print(f"✅ Found comparison data: {comparison_path}")
    
    # Generate report with AI
    success = generate_report_with_ai(comparison_path, api_key)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 AI-POWERED REPORT GENERATION: SUCCESS")
        print("✅ Executive report saved to output/executive_report.txt")
        print("✅ Insights saved to output/insights.csv")
    else:
        print("\n" + "=" * 50)
        print("❌ AI-POWERED REPORT GENERATION: FAILED")
        print("⚠️ Please check error messages above")

if __name__ == "__main__":
    main()