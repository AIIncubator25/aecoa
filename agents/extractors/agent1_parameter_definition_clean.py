"""
Agent 1 - Parameter Definition Agent
Extracts user-defined requirements from YAML and saves as parameters.csv
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import json


class ParameterDefinitionAgent:
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.prompt_log = []
        self.response_log = []
        # Custom prompt support - simplified to one editable prompt
        self.custom_combined_prompt = None
        self.custom_system_prompt = None
        self.custom_user_prompt = None
    
    def set_custom_prompts(self, combined_prompt: str = None, user_prompt: str = None):
        """Set custom prompt for this agent - using combined_prompt as the main editable prompt"""
        # Use combined_prompt as the main one, keep user_prompt parameter for backward compatibility
        self.custom_combined_prompt = combined_prompt
        # Keep these for backward compatibility but prioritize combined_prompt
        if combined_prompt:
            self.custom_system_prompt = None
            self.custom_user_prompt = None
        else:
            # Fallback to old system if combined_prompt not provided
            if user_prompt:
                self.custom_user_prompt = user_prompt

    def extract_parameters(self, yaml_content: str = None, yaml_file_path: str = None, selected_api_key: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Extract user-defined requirements from YAML and save as parameters.csv"""
        
        # Load YAML content
        if yaml_content:
            yaml_text = yaml_content
        elif yaml_file_path:
            try:
                with open(yaml_file_path, 'r', encoding='utf-8') as f:
                    yaml_text = f.read()
            except Exception as e:
                return False, {"error": f"Failed to read YAML file: {str(e)}"}
        else:
            return False, {"error": "Please provide your requirements as yaml_content or yaml_file_path"}
        
        # Build the analysis prompt - simplified to use one combined prompt
        if self.custom_combined_prompt:
            # Use the single combined prompt with YAML content
            combined_prompt = self.custom_combined_prompt.replace("{yaml_text}", yaml_text)
            # Split into system and user for API compatibility
            system_prompt = "You are Agent 1: Parameter Extraction Specialist."
            user_prompt = combined_prompt
        else:
            # Default combined approach - simple and clean
            system_prompt = (
                "You are Agent 1: Parameter Extraction Specialist. "
                "Extract measurable parameters from YAML requirements that can be verified against building drawings."
            )
            user_prompt = (
                f"Extract all measurable parameters from this YAML content:\n\n{yaml_text}\n\n"
                f"Return JSON format with 'parameters' array containing: "
                f"reference, parameter, value, unit, type, conditions, description. "
                f"Also include 'extraction_summary' with total count and structure info."
            )
        
        # Log the prompt
        self.prompt_log.append({
            "system": system_prompt,
            "user": user_prompt,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Call the AI provider
        try:
            if self.provider == "OpenAI":
                result = self._call_openai(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "GovTech":
                result = self._call_govtech(system_prompt, user_prompt, selected_api_key)
            else:
                result = {"error": f"Provider {self.provider} not supported in Agent 1"}
            
            # Log the response
            self.response_log.append({
                "result": result,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": "error" not in result
            })
            
            if "error" in result:
                return False, result
            
            # Process the result into DataFrame format
            parameters = result.get("parameters", [])
            extraction_summary = result.get("extraction_summary", {})
            
            # Create DataFrame and save CSV
            if parameters:
                df = pd.DataFrame(parameters)
                df.to_csv("parameters.csv", index=False)
                
                return True, {
                    "parameters_df": df,
                    "csv_saved": "parameters.csv",
                    "parameters_count": len(parameters),
                    "extraction_summary": extraction_summary,
                    "summary": {
                        "total_parameters": len(parameters),
                        "yaml_format": extraction_summary.get("yaml_format", "YAML structure analyzed"),
                        "sections_found": extraction_summary.get("main_sections", []),
                        "reference_system": extraction_summary.get("reference_system", "Various reference formats detected"),
                        "parameter_types": [p.get("type", "unknown") for p in parameters]
                    }
                }
            else:
                return False, {"error": "No parameters extracted from YAML"}
        
        except Exception as e:
            error_msg = f"Error in parameter extraction: {str(e)}"
            self.response_log.append({
                "error": error_msg,
                "timestamp": pd.Timestamp.now().isoformat(),
                "success": False
            })
            return False, {"error": error_msg}

    def _call_openai(self, system_prompt: str, user_prompt: str, api_key: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            from openai import OpenAI
            
            # Handle base URL for OpenAI
            try:
                import streamlit as st
                sec = st.secrets.get("openai", {})
                base_url = sec.get("base_url") if isinstance(sec, dict) else None
                if base_url and "govtext.gov.sg" in base_url.lower():
                    base_url = None  # Don't use GovTech URL for OpenAI
            except:
                base_url = None
            
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1
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
                "max_tokens": 4000,
                "temperature": 0.1
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
            
        except Exception as e:
            return {"error": f"GovTech call failed: {str(e)}"}

    def get_prompt_log(self) -> List[Dict[str, Any]]:
        return self.prompt_log
    
    def get_response_log(self) -> List[Dict[str, Any]]:
        return self.response_log
    
    def clear_logs(self):
        self.prompt_log = []
        self.response_log = []