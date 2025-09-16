"""
Agent 4 - Insights & Report Agent  
Generates executive summary and actionable recommendations from compliance analysis.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import json
import numpy as np


class InsightsReportAgent:
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.prompt_log = []
        self.response_log = []
        
        # Custom prompt support
        self.custom_system_prompt = None
        self.custom_user_prompt = None
        self.custom_combined_prompt = None
    
    def set_custom_prompts(self, combined_prompt: str = None, system_prompt: str = None, user_prompt: str = None):
        """Set custom prompts for Agent 4. Prefer combined if provided."""
        self.custom_combined_prompt = combined_prompt
        self.custom_system_prompt = system_prompt
        self.custom_user_prompt = user_prompt
    
    def generate_insights_report(self, comparisons_csv_path: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Generate comprehensive insights and recommendations from compliance analysis"""
        
        # Load comparison results
        try:
            comparisons_df = pd.read_csv(comparisons_csv_path)
        except Exception as e:
            return False, {"error": f"Failed to load comparisons CSV: {str(e)}"}
        
        # Analyze compliance patterns
        compliance_stats = self._analyze_compliance_patterns(comparisons_df)
        
        # Prepare data for AI analysis
        report_context = {
            "compliance_results": comparisons_df.to_dict('records'),
            "statistics": compliance_stats,
            "total_parameters": len(comparisons_df),
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Build the insights generation prompt
        # Use combined/system prompt preference
        if self.custom_combined_prompt:
            system_prompt = "You are Agent 4: Executive Insights Specialist."
        elif self.custom_system_prompt:
            system_prompt = self.custom_system_prompt
        else:
            system_prompt = (
                "You are Agent 4: Executive Business Intelligence & Strategic Insights Specialist. "
                "You are a senior business consultant with expertise in regulatory compliance, risk management, and strategic planning. "
                "Your mission is to transform technical compliance data into actionable business intelligence and strategic recommendations. "
                ""
                "🎯 EXECUTIVE INTELLIGENCE CAPABILITIES: "
            "• **Business Risk Analysis**: Translate technical compliance into business impact and financial risk "
            "• **Strategic Planning**: Develop prioritized action plans with timeline and resource considerations "
            "• **Regulatory Intelligence**: Understand compliance implications for permits, approvals, and operations "
            "• **Stakeholder Communication**: Create executive summaries suitable for C-level decision makers "
            "• **ROI Analysis**: Evaluate cost-benefit of compliance actions and risk mitigation "
            ""
            "🏢 BUSINESS CONTEXT EXPERTISE: "
            "• **Financial Impact**: Quantify costs of non-compliance vs remediation costs "
            "• **Operational Risk**: Assess business continuity and operational implications "
            "• **Regulatory Risk**: Evaluate permit delays, approvals, and legal exposure "
            "• **Market Risk**: Consider competitive implications and market positioning "
            "• **Reputation Risk**: Assess brand and stakeholder relationship impacts "
            ""
            "📊 ADVANCED ANALYTICAL INTELLIGENCE: "
            "• **Pattern Recognition**: Identify systemic issues and root causes across parameters "
            "• **Risk Stratification**: Categorize issues by business impact and urgency "
            "• **Trend Analysis**: Spot compliance trends and predictive indicators "
            "• **Resource Optimization**: Recommend efficient resource allocation for maximum impact "
            "• **Success Metrics**: Define KPIs and success criteria for compliance improvement "
            ""
            "🚀 STRATEGIC RECOMMENDATION ENGINE: "
            "• **Immediate Actions**: Critical items requiring urgent executive attention "
            "• **Short-term Strategic**: 30-90 day improvement initiatives with clear ROI "
            "• **Long-term Planning**: Strategic compliance roadmap aligned with business goals "
            "• **Contingency Planning**: Risk mitigation strategies and fallback options "
            "• **Success Optimization**: Leverage compliant areas as competitive advantages "
            ""
            "📋 COMPREHENSIVE OUTPUT FORMAT - Return JSON: "
            "{"
            "  \"executive_dashboard\": {"
            "    \"overall_status\": \"CRITICAL|HIGH_RISK|MEDIUM_RISK|LOW_RISK|COMPLIANT\","
            "    \"business_impact_score\": \"1-10 scale with business risk assessment\","
            "    \"compliance_grade\": \"A+|A|B+|B|C+|C|D+|D|F - executive grade\","
            "    \"key_success_metrics\": [\"quantifiable success indicators\"],"
            "    \"critical_alert_count\": \"number of items requiring immediate C-level attention\","
            "    \"regulatory_approval_likelihood\": \"high|medium|low - likelihood of regulatory approval\""
            "  },"
            "  \"executive_summary\": {"
            "    \"business_situation\": \"one-paragraph executive summary of compliance status\","
            "    \"key_achievements\": [\"areas where requirements are met or exceeded\"],"
            "    \"critical_concerns\": [\"issues requiring immediate executive action\"],"
            "    \"strategic_opportunities\": [\"areas where compliance can create competitive advantage\"],"
            "    \"financial_implications\": \"estimated cost impact of current compliance status\","
            "    \"timeline_urgency\": \"immediate|30-days|90-days - primary timeline for action\""
            "  },"
            "  \"business_risk_analysis\": {"
            "    \"critical_business_risks\": ["
            "      {"
            "        \"risk_category\": \"regulatory|operational|financial|reputational\","
            "        \"risk_description\": \"specific risk and business impact\","
            "        \"affected_parameters\": [\"parameter numbers causing this risk\"],"
            "        \"financial_exposure\": \"estimated cost range if not addressed\","
            "        \"mitigation_urgency\": \"immediate|high|medium|low\","
            "        \"mitigation_strategy\": \"recommended approach to address this risk\""
            "      }"
            "    ],"
            "    \"operational_impact\": \"how compliance status affects day-to-day operations\","
            "    \"regulatory_exposure\": \"potential regulatory consequences and timeline\","
            "    \"market_positioning\": \"competitive implications of compliance status\""
            "  },"
            "  \"strategic_action_plan\": {"
            "    \"immediate_actions\": ["
            "      {"
            "        \"action\": \"specific action required\","
            "        \"parameters_addressed\": [\"parameter numbers\"],"
            "        \"business_justification\": \"why this action is critical\","
            "        \"estimated_cost\": \"cost range for implementation\","
            "        \"timeline\": \"days/weeks for completion\","
            "        \"success_criteria\": \"how to measure success\","
            "        \"responsible_stakeholder\": \"who should lead this action\""
            "      }"
            "    ],"
            "    \"short_term_initiatives\": [\"30-90 day strategic improvements with ROI analysis\"],"
            "    \"long_term_roadmap\": [\"strategic compliance initiatives aligned with business goals\"],"
            "    \"resource_requirements\": \"estimated human and financial resources needed\","
            "    \"success_timeline\": \"projected timeline to achieve full compliance\""
            "  },"
            "  \"compliance_intelligence\": {"
            "    \"strength_analysis\": [\"areas of strong compliance to leverage\"],"
            "    \"vulnerability_assessment\": [\"systematic weaknesses requiring attention\"],"
            "    \"trend_indicators\": [\"patterns suggesting future compliance trajectory\"],"
            "    \"benchmark_comparison\": \"how this performance compares to industry standards\","
            "    \"improvement_opportunities\": [\"areas where investment will yield highest ROI\"]"
            "  },"
            "  \"stakeholder_communication\": {"
            "    \"c_suite_summary\": \"one-paragraph summary for C-level executives\","
            "    \"board_presentation_points\": [\"key points for board presentation\"],"
            "    \"regulatory_narrative\": \"explanation suitable for regulatory discussions\","
            "    \"investor_communication\": \"key points for investor/stakeholder communication\","
            "    \"internal_team_focus\": \"key messages for internal project teams\""
            "  },"
            "  \"success_metrics_kpis\": {"
            "    \"compliance_kpis\": [\"key performance indicators to track progress\"],"
            "    \"financial_metrics\": [\"financial KPIs related to compliance improvement\"],"
            "    \"operational_metrics\": [\"operational KPIs affected by compliance status\"],"
            "    \"timeline_milestones\": [\"key milestones and target dates\"],"
            "    \"success_definition\": \"clear definition of successful compliance achievement\""
            "  }"
            "}"
        )
        
        context_json = json.dumps(report_context, indent=2, default=str)
        
        # Use combined/user prompt if available, otherwise default
        if self.custom_combined_prompt:
            user_prompt = self.custom_combined_prompt.format(context_json=context_json)
        elif self.custom_user_prompt:
            user_prompt = self.custom_user_prompt.format(context_json=context_json)
        else:
            user_prompt = (
                f"🏢 **EXECUTIVE BUSINESS INTELLIGENCE MISSION** \\n"
                f"Transform technical compliance data into strategic business intelligence and actionable C-level recommendations.\\n\\n"
                f"📊 **COMPLIANCE DATA FOR ANALYSIS:** \\n"
                f"{context_json}\\n\\n"
            f"🎯 **BUSINESS INTELLIGENCE ANALYSIS FRAMEWORK:** \\n"
            f"**Phase 1: Business Context Assessment** \\n"
            f"• Understand the business implications of each compliance finding \\n"
            f"• Assess regulatory, operational, and financial risks \\n"
            f"• Identify strategic opportunities within compliance requirements \\n"
            f"• Evaluate market and competitive implications \\n\\n"
            f"**Phase 2: Risk Stratification & Impact Analysis** \\n"
            f"• **Critical Business Risks**: Items affecting regulatory approvals, safety, legal exposure \\n"
            f"• **High Impact Issues**: Significant operational or financial consequences \\n"
            f"• **Medium Priority Items**: Important but manageable compliance gaps \\n"
            f"• **Low Impact Areas**: Minor issues with minimal business consequence \\n\\n"
            f"**Phase 3: Strategic Pattern Recognition** \\n"
            f"• Identify systemic compliance patterns and root causes \\n"
            f"• Recognize compliance strengths that can be leveraged competitively \\n"
            f"• Spot trends indicating future compliance trajectory \\n"
            f"• Analyze resource efficiency opportunities \\n\\n"
            f"**Phase 4: Executive-Level Strategic Planning** \\n"
            f"• Develop prioritized action plans with clear business justification \\n"
            f"• Estimate costs, timelines, and resource requirements \\n"
            f"• Define success metrics and KPIs for compliance improvement \\n"
            f"• Align recommendations with broader business strategy \\n\\n"
            f"🚨 **COMPLIANCE STATUS BUSINESS INTERPRETATION:** \\n"
            f"• **✓ Meets**: Compliance strength - leverage as competitive advantage \\n"
            f"• **✓ Meets (marginal)**: Monitor closely - potential future risk \\n"
            f"• **✗ Below min**: Business risk - requires strategic remediation plan \\n"
            f"• **✗ Critical**: Executive emergency - immediate C-level attention required \\n"
            f"• **⚠ Check**: Business uncertainty - invest in verification to reduce risk \\n"
            f"• **⚠ Verify**: Likely compliant - confirm to strengthen business position \\n"
            f"• **− Not applicable**: Non-issue - allocate resources elsewhere \\n"
            f"• **− TBD**: Strategic dependency - plan for future determination \\n\\n"
            f"💼 **EXECUTIVE ANALYSIS REQUIREMENTS:** \\n"
            f"**Business Impact Assessment** \\n"
            f"• Financial exposure and cost-benefit analysis \\n"
            f"• Regulatory approval timeline and probability assessment \\n"
            f"• Operational continuity and efficiency implications \\n"
            f"• Market positioning and competitive advantage considerations \\n"
            f"• Stakeholder and reputation risk evaluation \\n\\n"
            f"**Strategic Recommendation Development** \\n"
            f"• Prioritize actions by business impact and resource efficiency \\n"
            f"• Provide clear ROI justification for compliance investments \\n"
            f"• Define specific success criteria and measurement approaches \\n"
            f"• Identify responsible stakeholders and escalation paths \\n"
            f"• Consider contingency plans and risk mitigation strategies \\n\\n"
            f"🎯 **KEY DELIVERABLES FOR EXECUTIVES:** \\n"
            f"1. **Dashboard Summary**: High-level status suitable for board presentation \\n"
            f"2. **Risk Analysis**: Business risks categorized by impact and urgency \\n"
            f"3. **Action Plan**: Prioritized recommendations with timelines and costs \\n"
            f"4. **Success Metrics**: KPIs to track compliance improvement progress \\n"
            f"5. **Stakeholder Communication**: Key messages for different audiences \\n\\n"
            f"⚡ **BUSINESS INTELLIGENCE SUCCESS FACTORS:** \\n"
            f"• **Strategic Alignment**: Align compliance with business objectives \\n"
            f"• **Resource Optimization**: Maximize compliance ROI and efficiency \\n"
            f"• **Risk Management**: Proactively address high-impact compliance risks \\n"
            f"• **Competitive Advantage**: Leverage compliance strengths strategically \\n"
            f"• **Stakeholder Value**: Create value for investors, regulators, and customers \\n\\n"
            f"🔮 **FORWARD-LOOKING ANALYSIS:** \\n"
            f"• Predict compliance trajectory and future risk evolution \\n"
            f"• Identify emerging compliance opportunities and threats \\n"
            f"• Recommend proactive strategies to stay ahead of requirements \\n"
            f"• Plan for scalability and business growth considerations \\n"
            f"• Integrate compliance strategy with broader business planning \\n\\n"
            f"Generate executive-grade business intelligence that enables confident strategic decision-making."
            )
        
        # Log the prompt
        self.prompt_log.append({
            "system": system_prompt,
            "user": user_prompt,
            "parameters_analyzed": len(comparisons_df),
            "compliance_stats": compliance_stats,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Call the AI provider
        try:
            if self.provider == "OpenAI":
                result = self._call_openai(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "GovTech":
                result = self._call_govtech(system_prompt, user_prompt, selected_api_key)
            else:
                result = {"error": f"Provider {self.provider} not supported in Agent 4"}
            
            # Log the response
            self.response_log.append({
                "result": result,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": "error" not in result
            })
            
            if "error" in result:
                return False, result
            
            # Generate the final report CSV with insights
            report_data = self._create_report_csv(result, comparisons_df)
            
            # Save report CSV
            if report_data:
                report_df = pd.DataFrame(report_data)
                report_df.to_csv("report.csv", index=False)
                
                return True, {
                    "insights": result,
                    "report_df": report_df,
                    "csv_saved": "report.csv",
                    "executive_summary": result.get("executive_summary", {}),
                    "recommendations": result.get("actionable_recommendations", {}),
                    "analysis_complete": True
                }
            else:
                return False, {"error": "Failed to generate report data"}
                
        except Exception as e:
            error_result = {"error": f"Agent 4 execution failed: {str(e)}"}
            self.response_log.append({
                "result": error_result,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": False
            })
            return False, error_result
    
    def _analyze_compliance_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in the compliance data"""
        try:
            # Count compliance statuses
            compliance_counts = {}
            if 'compliance' in df.columns:
                status_counts = df['compliance'].value_counts()
                compliance_counts = {
                    "meets": status_counts.get("✓ Meets", 0),
                    "below_min": status_counts.get("✗ Below min", 0),
                    "check": status_counts.get("⚠ Check", 0),
                    "not_applicable": status_counts.get("− Not applicable", 0)
                }
            
            # Calculate compliance rate
            total_applicable = compliance_counts.get("meets", 0) + compliance_counts.get("below_min", 0) + compliance_counts.get("check", 0)
            compliance_rate = (compliance_counts.get("meets", 0) / total_applicable * 100) if total_applicable > 0 else 0
            
            # Analyze source distribution
            source_counts = {}
            if 'source' in df.columns:
                source_counts = df['source'].value_counts().to_dict()
            
            return {
                "compliance_counts": compliance_counts,
                "compliance_rate": compliance_rate,
                "source_distribution": source_counts,
                "total_parameters": len(df),
                "applicable_parameters": total_applicable
            }
            
        except Exception as e:
            return {"error": f"Pattern analysis failed: {str(e)}"}
    
    def _create_report_csv(self, insights: Dict[str, Any], comparisons_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create structured report data for CSV output"""
        try:
            report_rows = []
            
            # Executive Summary Section
            exec_summary = insights.get("executive_summary", {})
            report_rows.extend([
                {"Section": "Executive Summary", "Item": "Overall Status", "Details": exec_summary.get("overall_compliance_status", "Unknown")},
                {"Section": "Executive Summary", "Item": "Compliance Score", "Details": exec_summary.get("compliance_score", "Not calculated")},
                {"Section": "Executive Summary", "Item": "Key Findings", "Details": "; ".join(exec_summary.get("key_findings", []))},
                {"Section": "Executive Summary", "Item": "Priority Actions", "Details": "; ".join(exec_summary.get("priority_actions_needed", []))}
            ])
            
            # Risk Assessment Section
            risk_assessment = insights.get("detailed_insights", {}).get("risk_assessment", {})
            for risk_level, items in risk_assessment.items():
                if items:
                    report_rows.append({
                        "Section": "Risk Assessment", 
                        "Item": risk_level.replace("_", " ").title(), 
                        "Details": "; ".join(items) if isinstance(items, list) else str(items)
                    })
            
            # Recommendations Section
            recommendations = insights.get("actionable_recommendations", {})
            for rec_type, items in recommendations.items():
                if items:
                    report_rows.append({
                        "Section": "Recommendations", 
                        "Item": rec_type.replace("_", " ").title(), 
                        "Details": "; ".join(items) if isinstance(items, list) else str(items)
                    })
            
            # Parameter Details Section
            for _, row in comparisons_df.iterrows():
                report_rows.append({
                    "Section": "Parameter Details",
                    "Item": f"Parameter {row.get('No', '')}: {row.get('Parameter', '')}",
                    "Details": f"Status: {row.get('compliance', 'Unknown')} | Value: {row.get('identified value', 'N/A')} | Source: {row.get('source', 'Unknown')}"
                })
            
            # Next Steps
            next_steps = insights.get("next_steps", [])
            if next_steps:
                for i, step in enumerate(next_steps, 1):
                    report_rows.append({
                        "Section": "Next Steps",
                        "Item": f"Step {i}",
                        "Details": step
                    })
            
            return report_rows
            
        except Exception as e:
            return [{"Section": "Error", "Item": "Report Generation Failed", "Details": str(e)}]
    
    def _call_openai(self, system_prompt: str, user_prompt: str, api_key: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            from openai import OpenAI
            import streamlit as st
            
            # Get base_url from secrets if available
            base_url = None
            try:
                sec = st.secrets.get("openai", {})
                base_url = sec.get("base_url")
                if base_url and "govtext.gov.sg" in base_url.lower():
                    base_url = None  # Don't use GovTech URL for OpenAI
            except Exception:
                pass
            
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            return {"error": f"OpenAI call failed: {str(e)}"}
    
    def _call_govtech(self, system_prompt: str, user_prompt: str, api_key: str) -> Dict[str, Any]:
        """Call GovTech LLMaaS API"""
        try:
            import requests
            
            url = f"https://llmaas.govtext.gov.sg/gateway/openai/deployments/{self.model}/chat/completions"
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 4000
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                # Enhanced error handling for GovTech API response parsing
                try:
                    response_json = response.json()
                    
                    # Check if response is empty or malformed
                    if not response_json:
                        return {"error": "GovTech API returned empty JSON response"}
                    
                    # Check for expected structure
                    choices = response_json.get("choices", [])
                    if not choices:
                        return {"error": f"GovTech API returned unexpected structure: {str(response_json)[:200]}"}
                    
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    
                    # Check if content is empty
                    if not content.strip():
                        return {"error": "GovTech API returned empty content"}
                    
                    # Try to parse the JSON content
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError as json_err:
                        return {"error": f"Invalid JSON in content: {str(json_err)}, Content preview: {content[:200]}"}
                        
                except json.JSONDecodeError as parse_err:
                    # Response is not valid JSON
                    content_preview = response.text[:200] if response.text else "No content"
                    return {"error": f"GovTech API response is not valid JSON: {str(parse_err)}, Response preview: {content_preview}"}
                    
            else:
                return {"error": f"GovTech API error: {response.status_code} - {response.text[:200]}"}
                
        except Exception as e:
            return {"error": f"GovTech call failed: {str(e)}"}
    
    def get_prompt_log(self) -> List[Dict[str, Any]]:
        """Return the prompt log for transparency"""
        return self.prompt_log
    
    def get_response_log(self) -> List[Dict[str, Any]]:
        """Return the response log for transparency"""
        return self.response_log
    
    def clear_logs(self):
        """Clear both prompt and response logs"""
        self.prompt_log = []
        self.response_log = []