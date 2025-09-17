"""
Agent 1 - Parameter Definition Agent
Extracts requirements from YAML and saves as parameters.csv
"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import json
import re


class ParameterDefinitionAgent:
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini") -> None:
        self.provider = provider
        self.model = model
        self.prompt_log: List[Dict[str, Any]] = []
        self.response_log: List[Dict[str, Any]] = []
        self.custom_combined_prompt: Optional[str] = None
        # Always use AI reasoning by default
        self.use_reasoning: bool = True

    def set_custom_prompts(self, combined_prompt: Optional[str] = None, use_reasoning: Optional[bool] = None, **_: Any) -> None:
        self.custom_combined_prompt = combined_prompt
        # Allow override but discourage setting use_reasoning to False
        if use_reasoning is not None:
            self.use_reasoning = bool(use_reasoning)

    def extract_parameters(
        self,
        yaml_content: Optional[str] = None,
        yaml_file_path: Optional[str] = None,
        selected_api_key: Optional[str] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        # Prioritize AI reasoning for structure agnosticism
        try:
            import os
            
            # Load YAML content from either string or file
            if yaml_content:
                yaml_text = yaml_content
            elif yaml_file_path:
                try:
                    with open(yaml_file_path, "r", encoding="utf-8") as f:
                        yaml_text = f.read()
                except Exception as e:
                    return False, {"error": f"Failed to read YAML file: {str(e)}"}
            elif os.path.exists("requirements_table.csv") and not self.use_reasoning:
                # Legacy fallback if table exists and reasoning is disabled
                return self._process_table_only_mode()
            else:
                return False, {"error": "Please provide YAML content or file path for parameter extraction."}

            # Enhanced AI reasoning mode with structure detection
            if self.custom_combined_prompt:
                system_prompt = "You are Agent 1: Parameter Extraction Specialist."
                user_prompt = self.custom_combined_prompt.replace("{yaml_text}", yaml_text)
            else:
                system_prompt = (
                    "You are an expert AI agent specializing in parsing engineering and regulatory documents in YAML format. "
                    "Your primary goal is to extract a list of parameter templates. Each template should be a self-contained object. "
                    "CRITICAL: You must respond ONLY with valid JSON format - no markdown, no explanations, just pure JSON."
                )
                user_prompt = (
                    f"Extract parameter templates from this YAML content into a JSON object with 'parameters' array.\n\n"
                    f"YAML CONTENT:\n```yaml\n{yaml_text}\n```\n\n"
                    f"REQUIREMENTS:\n"
                    f"1. Find objects that define measurable quantities (have 'source.description' and 'unit_conversion.unit' keys)\n"
                    f"2. Parameter name = object key (e.g., 'gfa_m2')\n"
                    f"3. Extract: parameter name, description, unit, value (empty string)\n"
                    f"4. Return ONLY this JSON structure:\n"
                    f"{{\n"
                    f'  "parameters": [\n'
                    f'    {{"parameter": "name", "description": "desc", "unit": "unit", "value": ""}}\n'
                    f"  ]\n"
                    f"}}\n\n"
                    f"NO other text, explanations, or markdown - ONLY the JSON object."
                )

            self.prompt_log.append({"system": system_prompt, "user": user_prompt, "timestamp": pd.Timestamp.now().isoformat()})

            if self.provider == "OpenAI":
                result = self._call_openai(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "GovTech":
                result = self._call_govtech(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "Ollama":
                result = self._call_ollama(system_prompt, user_prompt, selected_api_key)
            else:
                result = {"error": f"Provider {self.provider} not supported in Agent 1"}

            self.response_log.append({"result": result, "timestamp": pd.Timestamp.now().isoformat(), "success": "error" not in result})

            if "error" in result:
                # If AI reasoning fails and table exists, try table mode as fallback
                if os.path.exists("requirements_table.csv") and not "requirements_table.csv is empty" in result.get("error", ""):
                    return self._process_table_only_mode()
                return False, result

            parameters = result.get("parameters", [])
            extraction_summary = result.get("extraction_summary", {})

            if parameters:
                df = pd.DataFrame(parameters)
                df.to_csv("parameters.csv", index=False)
                return True, {
                    "parameters_df": df,
                    "csv_saved": "parameters.csv",
                    "parameters_count": len(parameters),
                    "extraction_summary": extraction_summary,
                    "ai_powered": True
                }
            else:
                # If no parameters extracted but table exists, try table mode
                if os.path.exists("requirements_table.csv"):
                    return self._process_table_only_mode()
                return False, {"error": "No parameters extracted from YAML"}

        except Exception as e:
            return False, {"error": f"Parameter extraction failed: {str(e)}"}
            
    def _process_table_only_mode(self) -> Tuple[bool, Dict[str, Any]]:
        """Legacy table-only mode as fallback"""
        try:
            import os
            if not os.path.exists("requirements_table.csv"):
                return False, {"error": "No requirements table found. Please upload YAML with a requirements table."}

            df = pd.read_csv("requirements_table.csv")
            if df.empty:
                return False, {"error": "requirements_table.csv is empty."}

            # Normalize expected columns
            columns_lower = {c.lower(): c for c in df.columns}
            def pick(*names):
                for n in names:
                    if n.lower() in columns_lower:
                        return columns_lower[n.lower()]
                return None
                
            col_no = pick("no", "id", "index", "#")
            col_ref = pick("reference", "ref", "code", "section", "clause")
            col_param = pick("parameter", "name", "title", "requirement", "item")
            col_value = pick("value", "requirement value", "spec", "specification", 
                           "min. rectilinear hs countable area", "min rectilinear area")
            col_unit = pick("unit", "units")
            col_type = pick("type", "category", "measurement type")
            col_cond = pick("conditions", "condition", "notes", "min. irregular hs countable area", "min irregular area")
            col_desc = pick("description", "detail", "context", "min. volume (m3)", "min volume")

            # Generic row-to-parameter mapping (no derived parameters, no unit defaults)
            out = []
            next_no = 1
            for _, row in df.iterrows():
                out.append({
                    "no": row.get(col_no) if col_no else next_no,
                    "reference": row.get(col_ref) if col_ref else "",
                    "parameter": row.get(col_param) if col_param else "",
                    "value": row.get(col_value) if col_value else "",
                    "unit": row.get(col_unit) if col_unit else "",
                    "type": row.get(col_type) if col_type else "other",
                    "conditions": row.get(col_cond) if col_cond else "",
                    "description": row.get(col_desc) if col_desc else ""
                })
                next_no += 1
            pdf = pd.DataFrame(out)
            pdf.to_csv("parameters.csv", index=False)
            return True, {
                "parameters_df": pdf,
                "csv_saved": "parameters.csv",
                "parameters_count": len(pdf),
                "extraction_summary": {"source": "requirements_table.csv", "columns": list(df.columns)},
                "ai_powered": False
            }
        except Exception as e:
            return False, {"error": f"Failed to build parameters from requirements_table.csv: {str(e)}"}

    def _call_openai(self, system_prompt: str, user_prompt: str, api_key: Optional[str]) -> Dict[str, Any]:
        try:
            from openai import OpenAI
            try:
                import streamlit as st
                sec = st.secrets.get("openai", {})
                base_url = sec.get("base_url") if isinstance(sec, dict) else None
                if base_url and "govtext.gov.sg" in (base_url or "").lower():
                    base_url = None
            except Exception:
                base_url = None
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            
            # Always try JSON mode first for structured extraction
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    max_tokens=4000,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
            except Exception as json_mode_error:
                # Some models don't support JSON mode, fall back to regular completion
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    max_tokens=4000,
                    temperature=0.1,
                )
            content = resp.choices[0].message.content or ""
            parsed = self._parse_json_response(content)
            if parsed is None:
                # Enhanced error message with content snippet
                content_snippet = content[:500] + "..." if len(content) > 500 else content
                return {
                    "error": "Failed to parse LLM response as JSON",
                    "raw": content_snippet,
                    "troubleshooting": "The AI response was not in valid JSON format. Try adjusting the prompt."
                }
            return parsed
        except Exception as e:
            return {"error": f"OpenAI call failed: {str(e)}"}

    def _call_govtech(self, system_prompt: str, user_prompt: str, api_key: Optional[str]) -> Dict[str, Any]:
        try:
            import requests
            
            # Ensure we use a compatible model for GovTech
            govtech_model = self.model
            if govtech_model not in ['gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini']:
                govtech_model = 'gpt-4'  # Default to gpt-4 for compatibility
            
            url = f"https://llmaas.govtext.gov.sg/gateway/openai/deployments/{govtech_model}/chat/completions"
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
            }
            
            # Add response_format for JSON only for compatible models
            if govtech_model in ['gpt-4', 'gpt-4o', 'gpt-4o-mini']:
                payload["response_format"] = {"type": "json_object"}
            
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            
            response_data = r.json()
            content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            if not content:
                return {"error": "GovTech returned empty response"}
                
            parsed = self._parse_json_response(content)
            if parsed is None:
                return {"error": f"GovTech returned non-JSON response", "raw": content[:2000]}
            return parsed
        except Exception as e:
            return {"error": f"GovTech call failed: {str(e)}"}

    def _call_ollama(self, system_prompt: str, user_prompt: str, api_key: Optional[str]) -> Dict[str, Any]:
        """Call Ollama local API"""
        try:
            import requests
            # Combine system and user prompts for Ollama
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model,
                "prompt": combined_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 4000,
                }
            }
            
            r = requests.post(url, json=payload, timeout=120)
            r.raise_for_status()
            
            response_data = r.json()
            content = response_data.get("response", "")
            
            if not content:
                return {"error": "Ollama returned empty response"}
            
            parsed = self._parse_json_response(content)
            if parsed is None:
                return {"error": f"Ollama returned non-JSON response", "raw": content[:2000]}
            return parsed
            
        except Exception as e:
            return {"error": f"Ollama call failed: {str(e)}. Make sure Ollama is running and the model '{self.model}' is available."}

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        if not content or not isinstance(content, str):
            return None
        text = content.strip()
        
        # 1) Direct parse of full response
        try:
            obj = json.loads(text)
            # Ensure we have the expected schema structure or wrap
            if isinstance(obj, list) and all(isinstance(item, dict) for item in obj[:3]):
                # List of parameters without wrapper
                return {"parameters": obj, "extraction_summary": {"structure": "direct parameter list"}}
            if isinstance(obj, dict):
                # Make sure we have parameters field
                if "parameters" not in obj and any(k in obj for k in ["rows", "items", "data"]):
                    # Try to find parameters under common keys
                    for param_key in ["rows", "items", "data"]:
                        if param_key in obj and isinstance(obj[param_key], list):
                            obj["parameters"] = obj[param_key]
                            break
                return obj
        except json.JSONDecodeError:
            pass
            
        # 2) Try with code fence removal  
        clean_text = self._strip_code_fences(text)
        try:
            obj = json.loads(clean_text)
            if isinstance(obj, list):
                return {"parameters": obj, "extraction_summary": {"structure": "code fenced list"}}
            if isinstance(obj, dict):
                if "parameters" not in obj and any(k in obj for k in ["rows", "items", "data"]):
                    for param_key in ["rows", "items", "data"]:
                        if param_key in obj and isinstance(obj[param_key], list):
                            obj["parameters"] = obj[param_key]
                            break
                return obj
        except json.JSONDecodeError:
            pass
            
        # 3) Try to extract only the JSON part from mixed content
        import re
        
        # Look for JSON object patterns
        json_patterns = [
            r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}',  # Nested braces
            r'\{[^}]*"parameters"[^}]*\[[^\]]*\][^}]*\}',         # parameters array pattern
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    obj = json.loads(match.strip())
                    if isinstance(obj, dict):
                        # Ensure parameters field exists
                        if "parameters" not in obj and any(k in obj for k in ["rows", "items", "data"]):
                            for param_key in ["rows", "items", "data"]:
                                if param_key in obj and isinstance(obj[param_key], list):
                                    obj["parameters"] = obj[param_key]
                                    break
                        # Validate that we have parameters
                        if "parameters" in obj and isinstance(obj["parameters"], list):
                            return obj
                except json.JSONDecodeError:
                    continue
                    
        # 4) Extract JSON array by balanced brackets with parameter wrapping
        array_block = self._extract_balanced_block(text, "[", "]")
        if array_block:
            try:
                arr = json.loads(array_block)
                if isinstance(arr, list) and all(isinstance(item, dict) for item in arr[:3]):
                    return {"parameters": arr, "extraction_summary": {"structure": "extracted array"}}
            except json.JSONDecodeError:
                pass
                
        return None

    def _strip_code_fences(self, s: str) -> str:
        # Remove leading/trailing triple backtick fences and language tags
        if s.startswith("```") and s.endswith("```"):
            inner = s[3:-3].strip()
            # Drop language hint like json, JSON, or others on first line
            first_newline = inner.find("\n")
            if first_newline != -1:
                first_line = inner[:first_newline].strip()
                if re.fullmatch(r"[a-zA-Z0-9_+-]+", first_line):
                    return inner[first_newline + 1 :].strip()
            return inner.strip()
        return s

    def _extract_balanced_block(self, s: str, open_ch: str, close_ch: str) -> Optional[str]:
        start = None
        depth = 0
        for i, ch in enumerate(s):
            if ch == open_ch:
                if depth == 0:
                    start = i
                depth += 1
            elif ch == close_ch and depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return s[start : i + 1]
        return None

    def get_prompt_log(self) -> List[Dict[str, Any]]:
        return self.prompt_log

    def get_response_log(self) -> List[Dict[str, Any]]:
        return self.response_log

    def clear_logs(self) -> None:
        self.prompt_log = []
        self.response_log = []