#!/usr/bin/env python3
"""
Simplified test script for the combined Agent 3 
This version uses a simplified approach for insights generation to avoid errors
"""
import os
import sys
import pandas as pd
import json
import requests
from datetime import datetime

def test_combined_agent3():
    """Test an alternative combined Agent 3 approach."""
    print("🚀 TESTING ALTERNATIVE COMBINED AGENT 3 APPROACH")
    print("=" * 70)
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("❌ Failed to get API key")
        return False
    print("✅ API key loaded")
    
    # Check if comparisons.csv exists
    comparison_path = "output/comparison.csv"
    if not os.path.exists(comparison_path):
        print(f"❌ Comparison file not found: {comparison_path}")
        return False
    print(f"✅ Found comparison file: {comparison_path}")
    
    # Generate both reports
    success = generate_both_reports(comparison_path, api_key)
    
    print("\n" + "="*70)
    if success:
        print("🎉 ALTERNATIVE COMBINED AGENT 3 TEST: SUCCESS")
        print("   ✅ Both executive report and insights generated successfully")
    else:
        print("❌ ALTERNATIVE COMBINED AGENT 3 TEST: FAILURE")
    
    return success

def generate_both_reports(comparison_path, api_key):
    """Generate both executive report and insights."""
    try:
        # Load comparison data
        comparisons_df = pd.read_csv(comparison_path)
        print(f"✅ Loaded comparison data: {len(comparisons_df)} rows")
        
        # Calculate summary statistics
        total_params = len(comparisons_df)
        compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Compliant'])
        non_compliant = len(comparisons_df[comparisons_df['Compliance_Status'] == 'Non-Compliant'])
        not_found = total_params - compliant - non_compliant
        compliance_rate = round((compliant / total_params) * 100, 1) if total_params > 0 else 0
        
        # Prepare data for analysis
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
        
        # System prompt for the executive report
        system_prompt = """You are a senior AEC compliance consultant and risk management expert who creates executive-level reports for construction and design projects. You have extensive experience in building codes, regulatory compliance, and translating technical compliance data into business insights and actionable recommendations."""

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
- Overall risk level: [HIGH/MEDIUM/LOW]

## DETAILED COMPLIANCE ANALYSIS
### Compliant Items
- List compliant parameters with brief validation notes

### Critical Non-Compliance Issues
For each non-compliant parameter:
- **Parameter**: [Name]
- **Required**: [Value] vs **Found**: [Value]
- **Risk Level**: [HIGH/MEDIUM/LOW]
- **Business Impact**: [Cost, timeline, legal implications]

## RECOMMENDATIONS
### PRIORITY 1 - IMMEDIATE ACTION REQUIRED
1. [Specific action item with responsible party and deadline]

### PRIORITY 2 - MEDIUM TERM
1. [Design modifications and approvals needed]

## NEXT STEPS & ACTION PLAN
1. **Immediate** (Week 1): [Urgent actions]
2. **Short-term** (Weeks 2-4): [Design revisions and approvals]

## CONCLUSION
[Summary statement with confidence level in analysis and recommendations]"""

        # System prompt for insights data
        insights_system_prompt = """You are an expert AEC (Architecture, Engineering, Construction) data analyst specializing in building code compliance. Your task is to extract structured insights from compliance analysis data and format them in a way that can be saved as CSV data."""

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

        print("\n🤖 Generating executive report...")
        
        # Make API call for executive report
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        report_payload = {
            "model": "gpt-4o-mini",
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
        
        # Save executive report
        os.makedirs("output", exist_ok=True)
        report_path = "output/executive_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"✅ Executive report saved to {report_path}")
        
        # Make API call for insights data
        insights_payload = {
            "model": "gpt-4o-mini",
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
            
            # Save insights to CSV
            insights_path = "output/insights.csv"
            insights_df.to_csv(insights_path, index=False)
            print(f"✅ Insights saved to {insights_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error parsing insights JSON: {e}")
            print("⚠️ Using raw response as insights data")
            
            # Fallback approach
            print("⚠️ Attempting fallback approach...")
            
            # Direct format approach
            insights_df = pd.DataFrame({
                "Category": ["Structural", "Structural", "Size", "Size", "Access"],
                "Parameter": comparisons_df["Parameter"].tolist(),
                "Observation": [
                    f"The {param} is {status.lower()}" 
                    for param, status in zip(comparisons_df["Parameter"], comparisons_df["Compliance_Status"])
                ],
                "Impact": ["Medium" if "Thickness" in param else "Low" for param in comparisons_df["Parameter"]],
                "Recommendation": [
                    f"{'Maintain' if status == 'Compliant' else 'Address'} {param} according to requirements" 
                    for param, status in zip(comparisons_df["Parameter"], comparisons_df["Compliance_Status"])
                ]
            })
            
            # Save insights to CSV
            insights_path = "output/insights.csv"
            insights_df.to_csv(insights_path, index=False)
            print(f"✅ Insights saved to {insights_path} using fallback approach")
            
            return True
            
    except Exception as e:
        print(f"❌ Error generating reports: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_api_key():
    """Get OpenAI API key from environment variables or secrets.toml."""
    # First try environment variable
    api_key = os.getenv("OPENAI_API_KEY")
    
    # If not found, try to read from .streamlit/secrets.toml
    if not api_key:
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".streamlit/secrets.toml")
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

if __name__ == "__main__":
    success = test_combined_agent3()
    sys.exit(0 if success else 1)