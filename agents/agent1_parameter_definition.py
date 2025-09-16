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
                    "Your primary goal is to extract a list of parameter templates. Each template should be a self-contained object."
                )
                user_prompt = (
                    f"Analyze the following YAML content and extract all parameter templates into a list of JSON objects. Each object represents a distinct parameter (a row).\n\n"
                    f"YAML CONTENT:\n```yaml\n{yaml_text}\n```\n\n"
                    f"IMPORTANT INSTRUCTIONS:\n"
                    f"1.  Scan the YAML for objects that define measurable quantities (parameter templates).\n"
                    f"2.  A parameter template is identifiable by its contents, typically having 'source.description' and 'unit_conversion.unit' keys.\n"
                    f"3.  The parameter's name is the key of the template object itself (e.g., 'gfa_m2').\n"
                    f"4.  For each parameter template you find, create one complete JSON object containing all its details.\n"
                    f"5.  The fields for each object should be 'parameter' (the name), 'description', 'unit', and 'value' (which should be an empty string).\n"
                    f"6.  Do NOT group parameters by their attributes (like putting all descriptions in one list). Each object must be complete.\n"
                    f"7.  Return a single JSON object with a 'parameters' key. The value of this key must be an array of the parameter objects you created.\n\n"
                    f"Example of the required row-based output format:\n"
                    f"{{\n"
                    f'  "parameters": [\n'
                    f'    {{ "parameter": "gfa_m2", "description": "Gross Floor Area (project input)", "unit": "m²", "value": "" }},\n'
                    f'    {{ "parameter": "hs_enclosed_volume_m3", "description": "Entire enclosed HS volume (2.10(b))", "unit": "m³", "value": "" }},\n'
                    f'    {{ "parameter": "hs_ceiling_slab_thickness_mm", "description": "HS ceiling slab thickness", "unit": "mm", "value": "" }}\n'
                    f"  ]\n"
                    f"}}"
                )

            self.prompt_log.append({"system": system_prompt, "user": user_prompt, "timestamp": pd.Timestamp.now().isoformat()})

            if self.provider == "OpenAI":
                result = self._call_openai(system_prompt, user_prompt, selected_api_key)
            elif self.provider == "GovTech":
                result = self._call_govtech(system_prompt, user_prompt, selected_api_key)
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
            url = f"https://llmaas.govtext.gov.sg/gateway/openai/deployments/{self.model}/chat/completions"
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 4000,
                "temperature": 0.1,
            }
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"] or ""
            parsed = self._parse_json_response(content)
            if parsed is None:
                return {"error": f"GovTech returned non-JSON response", "raw": content[:2000]}
            return parsed
        except Exception as e:
            return {"error": f"GovTech call failed: {str(e)}"}

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
            
        # 3) Extract JSON object by balanced braces
        brace_block = self._extract_balanced_block(text, "{", "}")
        if brace_block:
            try:
                obj = json.loads(brace_block)
                if isinstance(obj, dict):
                    if "parameters" not in obj and any(k in obj for k in ["rows", "items", "data"]):
                        for param_key in ["rows", "items", "data"]:
                            if param_key in obj and isinstance(obj[param_key], list):
                                obj["parameters"] = obj[param_key]
                                break
                    return obj
            except json.JSONDecodeError:
                pass
                
        # 4) Extract JSON array by balanced brackets with parameter wrapping
        array_block = self._extract_balanced_block(text, "[", "]")
        if array_block:
            try:
                arr = json.loads(array_block)
                if isinstance(arr, list) and all(isinstance(item, dict) for item in arr[:3]):
                    return {"parameters": arr, "extraction_summary": {"structure": "extracted array"}}
            except json.JSONDecodeError:
                pass
                
        # 5) Last resort - try to find JSON object with regex
        import re
        json_match = re.search(r'\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\}', text)
        if json_match:
            try:
                obj = json.loads(json_match.group(0))
                if isinstance(obj, dict):
                    if "parameters" not in obj and any(k in obj for k in ["rows", "items", "data"]):
                        for param_key in ["rows", "items", "data"]:
                            if param_key in obj and isinstance(obj[param_key], list):
                                obj["parameters"] = obj[param_key]
                                break
                    return obj
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