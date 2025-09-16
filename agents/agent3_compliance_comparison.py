"""
Agent 3 - Compliance Comparison Agent
Merges requirements with analysis data and determines compliance status.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import json
import numpy as np


class ComplianceComparisonAgent:
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
        """Set custom prompts for this agent. Prefer combined if provided."""
        self.custom_combined_prompt = combined_prompt
        self.custom_system_prompt = system_prompt
        self.custom_user_prompt = user_prompt
    
    def compare_compliance(self, parameters_csv_path: str, analysis_csv_path: str, selected_api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Compare analysis results against requirements to determine compliance"""
        
        # Load data files
        try:
            parameters_df = pd.read_csv(parameters_csv_path)
            analysis_df = pd.read_csv(analysis_csv_path)
        except Exception as e:
            return False, {"error": f"Failed to load CSV files: {str(e)}"}
        
        # Merge the dataframes
        try:
            # Match by parameter name, as it's the common field
            merged_df = parameters_df.merge(
                analysis_df, 
                on='parameter', 
                how='left',
                suffixes=('_req', '_found')
            )
        except Exception as e:
            return False, {"error": f"Failed to merge data: {str(e)}"}
        
        # Prepare data for AI analysis
        comparison_data = []
        for _, row in merged_df.iterrows():
            comparison_data.append({
                "no": row.get("no"),
                "parameter": row.get("parameter"),
                "min_value": row.get("min_value"),
                "unit": row.get("unit"),
                "category": row.get("category"),
                "found_value": row.get("found_value", "not found"),
                "location": row.get("location", "N/A"),
                "confidence": row.get("confidence", "N/A")
            })
        
        # Build the compliance analysis prompt using combined or custom/default prompts
        if self.custom_combined_prompt:
            system_prompt = "You are Agent 3: Compliance Analysis Specialist."
        else:
            # Default system prompt
            system_prompt = (
                "You are Agent 3: Expert Compliance Analysis Specialist. "
                "You are a certified compliance expert with deep knowledge of building codes, regulations, and standards. "
                "Your mission is to perform intelligent compliance comparison between requirements and actual measurements. "
                ""
                "🎯 CORE EXPERTISE: "
                "• Regulatory Compliance Intelligence: Understand building codes, safety standards, accessibility requirements "
            "• Measurement Analysis: Evaluate numerical compliance with tolerance considerations "
            "• Risk Assessment: Identify compliance risks and their business/safety implications "
            "• Engineering Judgment: Apply professional judgment for ambiguous or edge cases "
            "• Confidence-Weighted Analysis: Factor measurement confidence into compliance decisions "
            ""
            "⚖️ INTELLIGENT COMPLIANCE ANALYSIS PROCESS: "
            "1. **Parameter Assessment**: Understand the regulatory intent and safety purpose "
            "2. **Measurement Evaluation**: Analyze found values against requirements with engineering judgment "
            "3. **Confidence Integration**: Weight compliance decisions based on measurement reliability "
            "4. **Risk Stratification**: Categorize non-compliance by safety and regulatory impact "
            "5. **Context Consideration**: Apply domain knowledge about tolerance, interpretation, and exceptions "
            ""
            "🔬 ADVANCED COMPLIANCE INTELLIGENCE: "
            "• **Numerical Analysis**: Precise comparison with unit conversion and tolerance consideration "
            "• **Qualitative Assessment**: Evaluate descriptive requirements and conditional compliance "
            "• **Uncertainty Handling**: Manage low-confidence measurements and ambiguous findings "
            "• **Risk Contextualization**: Understand which non-compliance poses critical vs minor risks "
            "• **Professional Interpretation**: Apply industry standards and best practices "
            ""
            "📊 COMPLIANCE STATUS DEFINITIONS: "
            "• **✓ Meets**: Value clearly meets or exceeds requirement with high confidence "
            "• **✓ Meets (marginal)**: Value meets requirement but close to limit or with some uncertainty "
            "• **✗ Below min**: Value definitively below requirement - requires immediate action "
            "• **✗ Critical**: Value significantly below requirement - poses safety/regulatory risk "
            "• **⚠ Check**: Uncertain compliance due to low confidence, ambiguous data, or interpretation needed "
            "• **⚠ Verify**: Measurement needs verification but initial indication suggests compliance "
            "• **− Not applicable**: Parameter not found, not relevant, or exempted "
            "• **− TBD**: Parameter requires future determination or additional information "
            ""
            "🚨 RISK-BASED COMPLIANCE ASSESSMENT: "
            "• **Critical Risk**: Life safety, structural integrity, major code violations "
            "• **High Risk**: Significant regulatory non-compliance, accessibility issues "
            "• **Medium Risk**: Minor code deviations, performance shortfalls "
            "• **Low Risk**: Documentation issues, minor specification variances "
            ""
            "📋 OUTPUT FORMAT - Return JSON: "
            "{"
            "  \"compliance_analysis\": ["
            "    {"
            "      \"no\": \"parameter number from requirements\","
            "      \"parameter\": \"requirement description\","
            "      \"requirement_value\": \"required value/condition from standards\","
            "      \"identified_value\": \"value found in drawings or 'not found'\","
            "      \"measurement_source\": \"JPG|DXF|Calculated|Schedule|Not Found\","
            "      \"measurement_confidence\": \"confidence level from Agent 2\","
            "      \"compliance_status\": \"detailed status from definitions above\","
            "      \"compliance_reasoning\": \"engineering analysis of why this status was assigned\","
            "      \"numerical_comparison\": \"mathematical analysis if applicable (e.g., '150 > 120: compliant')\","
            "      \"risk_level\": \"critical|high|medium|low|none\","
            "      \"risk_implications\": \"what this compliance status means for safety/regulatory/business\","
            "      \"recommendation\": \"specific action recommended for this parameter\","
            "      \"tolerance_applied\": \"any engineering tolerance or interpretation used\","
            "      \"verification_needed\": \"true|false - whether additional verification is recommended\""
            "    }"
            "  ],"
            "  \"overall_assessment\": {"
            "    \"compliance_grade\": \"A|B|C|D|F - overall performance grade\","
            "    \"critical_issues_count\": \"number of critical non-compliance items\","
            "    \"risk_summary\": \"executive summary of primary risks identified\","
            "    \"regulatory_status\": \"likely regulatory approval status\","
            "    \"safety_assessment\": \"overall safety compliance evaluation\""
            "  },"
            "  \"compliance_statistics\": {"
            "    \"total_parameters\": 0,"
            "    \"meets_count\": 0,"
            "    \"meets_marginal_count\": 0,"
            "    \"below_min_count\": 0,"
            "    \"critical_count\": 0,"
            "    \"check_count\": 0,"
            "    \"verify_count\": 0,"
            "    \"not_applicable_count\": 0,"
            "    \"compliance_percentage\": \"percentage meeting requirements\""
            "  },"
            "  \"priority_matrix\": {"
            "    \"immediate_action_required\": [\"parameters requiring urgent attention\"],"
            "    \"verification_needed\": [\"parameters needing additional measurement/confirmation\"],"
            "    \"monitor_closely\": [\"parameters meeting requirements but warrant monitoring\"],"
            "    \"compliant_confirmed\": [\"parameters with solid compliance confirmation\"]"
            "  }"
            "}"
        )
        
        comparison_context = json.dumps(comparison_data, indent=2)
        
        # Use combined or custom user prompt if available, otherwise default
        if self.custom_combined_prompt:
            user_prompt = self.custom_combined_prompt.format(comparison_context=comparison_context)
        elif self.custom_user_prompt:
            user_prompt = self.custom_user_prompt.format(comparison_context=comparison_context)
        else:
            user_prompt = (
                f"🏗️ **COMPLIANCE ANALYSIS MISSION** \\n"
                f"Perform expert compliance analysis comparing requirements against actual measurements.\\n\\n"
                f"📊 **DATA FOR ANALYSIS:**\\n"
                f"{comparison_context}\\n\\n"
            f"⚖️ **INTELLIGENT ANALYSIS PROTOCOL:** \\n"
            f"**Phase 1: Parameter Understanding** \\n"
            f"• Understand the regulatory intent and safety purpose of each requirement \\n"
            f"• Identify the measurement type (area, dimension, clearance, count, etc.) \\n"
            f"• Consider applicable building codes, standards, and best practices \\n"
            f"• Assess the criticality of each parameter for safety and compliance \\n\\n"
            f"**Phase 2: Measurement Evaluation** \\n"
            f"• Analyze the found value against the requirement with engineering judgment \\n"
            f"• Apply appropriate tolerances and interpretation guidelines \\n"
            f"• Consider measurement confidence and reliability factors \\n"
            f"• Evaluate unit consistency and conversion needs \\n\\n"
            f"**Phase 3: Risk-Based Compliance Assessment** \\n"
            f"• **Critical Risk Parameters**: Life safety, structural integrity, fire egress \\n"
            f"  → Any non-compliance requires immediate attention \\n"
            f"• **High Risk Parameters**: Accessibility, major code requirements \\n"
            f"  → Non-compliance has significant regulatory implications \\n"
            f"• **Medium Risk Parameters**: Performance standards, minor code items \\n"
            f"  → Non-compliance should be addressed but not urgent \\n"
            f"• **Low Risk Parameters**: Documentation, minor specifications \\n"
            f"  → Non-compliance has minimal impact \\n\\n"
            f"**Phase 4: Professional Engineering Judgment** \\n"
            f"• Apply industry standards and professional interpretation \\n"
            f"• Consider measurement uncertainty and confidence levels \\n"
            f"• Evaluate edge cases with engineering best practices \\n"
            f"• Provide actionable recommendations for each parameter \\n\\n"
            f"🔬 **DETAILED COMPLIANCE ASSESSMENT GUIDE:** \\n"
            f"**For Each Parameter, Execute:** \\n"
            f"1. **Requirement Analysis**: What does this parameter ensure/protect? \\n"
            f"2. **Value Comparison**: Mathematical/qualitative comparison \\n"
            f"3. **Confidence Integration**: How reliable is the measurement? \\n"
            f"4. **Risk Assessment**: What's the impact of non-compliance? \\n"
            f"5. **Professional Judgment**: Apply engineering interpretation \\n"
            f"6. **Actionable Recommendation**: What specific action is needed? \\n\\n"
            f"🎯 **COMPLIANCE DECISION MATRIX:** \\n"
            f"**✓ Meets**: Value clearly satisfies requirement \\n"
            f"  → High confidence + meets/exceeds requirement \\n"
            f"**✓ Meets (marginal)**: Value meets requirement but close to limit \\n"
            f"  → Medium confidence or near-boundary compliance \\n"
            f"**✗ Below min**: Value definitively below requirement \\n"
            f"  → Clear non-compliance requiring remedial action \\n"
            f"**✗ Critical**: Significant non-compliance with safety implications \\n"
            f"  → Immediate action required for safety/code compliance \\n"
            f"**⚠ Check**: Uncertain compliance needing verification \\n"
            f"  → Low confidence, ambiguous data, or interpretation needed \\n"
            f"**⚠ Verify**: Likely compliant but verification recommended \\n"
            f"  → Medium confidence with positive indication \\n"
            f"**− Not applicable**: Parameter not relevant or found \\n"
            f"  → Not found in drawings or not applicable to this project \\n"
            f"**− TBD**: Requires future determination \\n"
            f"  → Depends on future design decisions or additional data \\n\\n"
            f"🚨 **CRITICAL SUCCESS FACTORS:** \\n"
            f"• **Engineering Rigor**: Apply professional engineering judgment \\n"
            f"• **Risk Awareness**: Prioritize safety-critical and regulatory parameters \\n"
            f"• **Confidence Integration**: Weight decisions by measurement reliability \\n"
            f"• **Actionable Results**: Provide clear, specific recommendations \\n"
            f"• **Business Context**: Consider regulatory, safety, and cost implications \\n\\n"
            f"⚡ **SPECIAL CONSIDERATIONS:** \\n"
            f"• **Unit Conversions**: Handle metric/imperial conversions accurately \\n"
            f"• **Tolerance Application**: Apply reasonable engineering tolerances \\n"
            f"• **Confidence Weighting**: Lower confidence = more conservative compliance \\n"
            f"• **Regulatory Context**: Consider local codes and jurisdictional requirements \\n"
            f"• **Edge Case Handling**: Apply professional judgment for ambiguous situations \\n\\n"
            f"Generate comprehensive, engineering-grade compliance analysis."
            )
        
        # Log the prompt
        self.prompt_log.append({
            "system": system_prompt,
            "user": user_prompt,
            "comparison_count": len(comparison_data),
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Call the AI provider
        try:
            if self.provider == "OpenAI":
                result = self._call_openai(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "GovTech":
                result = self._call_govtech(system_prompt, user_prompt, selected_api_key)
            else:
                result = {"error": f"Provider {self.provider} not supported in Agent 3"}
            
            # Log the response
            self.response_log.append({
                "result": result,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": "error" not in result
            })
            
            if "error" in result:
                return False, result
            
            # Process the result and create final CSV with enhanced format
            compliance_analysis = result.get("compliance_analysis", [])
            overall_assessment = result.get("overall_assessment", {})
            compliance_statistics = result.get("compliance_statistics", {})
            
            # Backward compatibility with old format
            if not compliance_analysis and "compliance_results" in result:
                compliance_analysis = result["compliance_results"]
            
            if compliance_analysis:
                # Create the final comparison DataFrame with enhanced columns
                final_rows = []
                
                for comp in compliance_analysis:
                    # Find the original parameter data
                    param_no = comp.get('no')
                    param_row = parameters_df[parameters_df['no'] == param_no]
                    if not param_row.empty:
                        param_data = param_row.iloc[0].to_dict()
                        
                        # Build the complete row with enhanced compliance data
                        final_row = {
                            "No": comp.get("no"),
                            "Parameter": comp.get("parameter"),
                            "Requirement": comp.get("requirement_value") or param_data.get("value", ""),
                            "Unit": param_data.get("unit"),
                            "Found_Value": comp.get("identified_value"),
                            "Source": comp.get("measurement_source") or comp.get("source"),  # backward compatibility
                            "Confidence": comp.get("measurement_confidence"),
                            "Compliance_Status": comp.get("compliance_status") or comp.get("compliance"),  # backward compatibility
                            "Risk_Level": comp.get("risk_level"),
                            "Compliance_Reasoning": comp.get("compliance_reasoning"),
                            "Numerical_Comparison": comp.get("numerical_comparison") or comp.get("numeric_comparison"),  # backward compatibility
                            "Risk_Implications": comp.get("risk_implications"),
                            "Recommendation": comp.get("recommendation"),
                            "Tolerance_Applied": comp.get("tolerance_applied"),
                            "Verification_Needed": comp.get("verification_needed")
                        }
                        final_rows.append(final_row)
                
                # Create DataFrame and save CSV
                final_df = pd.DataFrame(final_rows)
                final_df.to_csv("comparisons.csv", index=False)
                
                return True, {
                    "compliance_df": final_df,
                    "overall_assessment": overall_assessment,
                    "compliance_statistics": compliance_statistics,
                    "priority_matrix": result.get("priority_matrix", {}),
                    "csv_saved": "comparisons.csv",
                    "total_parameters": len(compliance_analysis),
                    "compliance_grade": overall_assessment.get("compliance_grade", "Unknown"),
                    "critical_issues": overall_assessment.get("critical_issues_count", 0)
                }
            else:
                return False, {"error": "No compliance analysis results generated"}
                
        except Exception as e:
            error_result = {"error": f"Agent 3 execution failed: {str(e)}"}
            self.response_log.append({
                "result": error_result,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": False
            })
            return False, error_result
    
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
                max_tokens=3000
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
                "max_tokens": 3000
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