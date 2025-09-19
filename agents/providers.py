from __future__ import annotations
import base64
import json
import os
import requests
from typing import Dict, Any, Tuple
from .model_manager import model_manager, ModelInfo

# Legacy defaults - now managed dynamically by model_manager
DEFAULTS = {
    "GovTech": {"model": "gpt-4o", "base_url": "https://llmaas.govtext.gov.sg/gateway"},
    "OpenAI": {"model": "gpt-4o", "base_url": None},
    "Ollama": {"model": "llama3.2:latest", "base_url": None},
}

class call_provider:
    @staticmethod
    def auto_select(provider_hint: str | None, model_hint: str | None) -> Tuple[str, str]:
        """Auto-select provider and model with dynamic model detection"""
        provider = provider_hint or "GovTech"
        
        if model_hint:
            # Use specified model if provided
            model = model_hint
        else:
            # Try to get recommended model for compliance analysis
            recommended = model_manager.get_recommended_model("compliance_analysis", provider)
            if recommended:
                model = recommended.name
            else:
                # Fall back to legacy defaults
                model = DEFAULTS[provider]["model"]
        
        return provider, model
    
    @staticmethod
    def get_available_models(provider: str, api_key: str = None) -> Dict[str, ModelInfo]:
        """Get available models for a specific provider"""
        provider_configs = {}
        
        if api_key:
            if provider == "OpenAI":
                provider_configs['openai'] = {'api_key': api_key}
            elif provider == "GovTech":
                provider_configs['govtech'] = {'api_key': api_key}
        
        all_models = model_manager.get_all_models(provider_configs)
        return all_models.get(provider, {})

    @staticmethod
    def extract_from_image(image_bytes: bytes, provider: str, model: str) -> Dict[str, Any]:
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{img_b64}"
        system = (
            "You are an AEC compliance analyzer. Extract measurements from building drawings to populate a compliance table. "
            "Your task is to find values for the 'identified value', 'source', and 'compliance' columns. "
            "Return valid JSON only with this structure: "
            "{"
            "  \"analysis_results\": ["
            "    {"
            "      \"no\": 1, "
            "      \"identified_value\": \"actual measured value or 'not found'\", "
            "      \"source\": \"JPG|DXF|Both|Calculated\", "
            "      \"compliance\": \"✓ Meets|✗ Below min|⚠ Check|− Not applicable\" "
            "    }"
            "  ],"
            "  \"summary\": \"Brief analysis summary\""
            "}"
        )
        user = (
            "Analyze this building drawing and extract measurements for compliance checking. "
            "Look for:\n"
            "1. HS (Household Shelter) floor areas\n"
            "2. Height clearances (1500mm min)\n"
            "3. Ceiling slab thickness (300mm min)\n"
            "4. Staircase waist thickness (300mm min)\n"
            "5. Ventilation opening distances (700mm min)\n\n"
            "For each parameter you can identify:\n"
            "- Extract the actual measured value\n"
            "- Note if it came from JPG, DXF, both, or was calculated\n"
            "- Compare against requirements to determine compliance\n\n"
            "If you cannot find a measurement, set identified_value to 'not found' and compliance to '− Not applicable'."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": user},
                {"type": "image_url", "image_url": {"url": data_uri}},
            ]},
        ]
        return call_provider._dispatch(messages, provider, model)

    @staticmethod
    def extract_from_dxf(dxf_bytes: bytes, provider: str, model: str) -> Dict[str, Any]:
        system = (
            "You are an AEC compliance analyzer for DXF technical drawings. Extract measurements to populate a compliance table. "
            "Your task is to find values for the 'identified value', 'source', and 'compliance' columns. "
            "Return valid JSON only with this structure: "
            "{"
            "  \"analysis_results\": ["
            "    {"
            "      \"no\": 1, "
            "      \"identified_value\": \"actual measured value or 'not found'\", "
            "      \"source\": \"DXF|Calculated\", "
            "      \"compliance\": \"✓ Meets|✗ Below min|⚠ Check|− Not applicable\" "
            "    }"
            "  ],"
            "  \"summary\": \"Brief analysis summary\""
            "}"
        )
        user = (
            "Analyze DXF drawing data to extract building measurements for compliance checking. "
            "Look for:\n"
            "1. HS (Household Shelter) floor areas and volumes\n"
            "2. Height clearances (min 1500mm)\n"
            "3. Ceiling slab thickness (min 300mm)\n"
            "4. Staircase waist thickness (min 300mm)\n"
            "5. Ventilation opening distances (min 700mm)\n\n"
            "Extract dimensions, calculate areas/volumes where needed, and assess compliance against minimums. "
            "If a measurement cannot be determined from DXF data, mark as 'not found'."
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return call_provider._dispatch(messages, provider, model)

    @staticmethod
    def _dispatch(messages, provider: str, model: str) -> Dict[str, Any]:
        if provider == "Ollama":
            try:
                # For Ollama, use the chat completions format for vision models
                # Use llava model for vision capabilities instead of llama3.2
                vision_model = "llava:latest" if "llava" not in model.lower() else model
                
                # Ollama expects different message format for images
                # Check if messages contain image data
                ollama_messages = []
                for msg in messages:
                    if isinstance(msg.get("content"), list):
                        # OpenAI format - convert to Ollama format
                        text_parts = [item["text"] for item in msg["content"] if item.get("type") == "text"]
                        image_parts = [item["image_url"]["url"] for item in msg["content"] if item.get("type") == "image_url"]
                        
                        content = " ".join(text_parts)
                        ollama_msg = {"role": msg["role"], "content": content}
                        
                        # Add images if present
                        if image_parts:
                            # Extract base64 from data URLs
                            images = []
                            for img_url in image_parts:
                                if img_url.startswith("data:image/"):
                                    base64_part = img_url.split(",")[1]
                                    images.append(base64_part)
                            if images:
                                ollama_msg["images"] = images
                        
                        ollama_messages.append(ollama_msg)
                    else:
                        # Already in simple format
                        ollama_messages.append(msg)
                
                payload = {
                    "model": vision_model, 
                    "messages": ollama_messages,
                    "stream": False,
                    "format": "json"  # Request JSON output
                }
                r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
                if r.status_code == 200:
                    response_data = r.json()
                    txt = response_data.get("message", {}).get("content", "{}")
                    try:
                        return json.loads(txt)
                    except Exception:
                        return {"summary": {"key_findings": [txt]}}
                return {"error": f"Ollama HTTP {r.status_code}: {r.text[:200]}"}
            except Exception as e:
                return {"error": f"Ollama error: {e}"}
        if provider == "OpenAI":
            try:
                from openai import OpenAI
                # Prefer BYOK from Streamlit secrets; fallback to env OPENAI_API_KEY
                api_key = None
                base_url = None
                try:
                    import streamlit as st
                    sec = st.secrets.get("openai", {})
                    # For OpenAI engine, prioritize OPENAI_API_KEY over GOVTECH_API_KEY
                    api_key = sec.get("OPENAI_API_KEY") or sec.get("BYOK_api_key") or sec.get("api_key")
                    base_url = sec.get("base_url")
                except Exception:
                    pass
                # If base_url points to GovTech, ignore it for OpenAI
                if base_url and "govtext.gov.sg" in base_url.lower():
                    base_url = None
                # Choose key strictly for OpenAI (avoid using GovTech key by mistake)
                if not api_key:
                    env_openai = os.getenv("OPENAI_API_KEY")
                    if env_openai:
                        api_key = env_openai
                if not api_key:
                    return {"error": "No OpenAI key found. Set secrets.openai.OPENAI_API_KEY or OPENAI_API_KEY for Engine=OpenAI."}
                client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                content = resp.choices[0].message.content
                try:
                    return json.loads(content)
                except Exception:
                    return {"summary": {"key_findings": [content]}}
            except Exception as e:
                return {"error": f"OpenAI error: {e}"}
        # GovTech default
        try:
            url = f"https://llmaas.govtext.gov.sg/gateway/openai/deployments/{model}/chat/completions"
            headers = {"api-key": _get_key(), "Content-Type": "application/json"}
            payload = {"messages": messages, "temperature": 0.0}
            if not any(f in model.lower() for f in ["gpt-5", "vision"]):
                payload["response_format"] = {"type": "json_object"}
            r = requests.post(url, headers=headers, json=payload, timeout=180)
            if r.status_code == 200:
                data = r.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                try:
                    return json.loads(content) if content else {}
                except Exception:
                    return {"summary": {"key_findings": [content]}}
            return {"error": f"GovTech HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": f"GovTech error: {e}"}

def _get_key() -> str:
    # Keep aligned with app.py get_api_key fallback
    try:
        import streamlit as st
        # Prefer explicit govtech section, fall back to openai uppercase entries
        sec_gov = st.secrets.get("govtech", {}) if hasattr(st, "secrets") else {}
        sec_open = st.secrets.get("openai", {}) if hasattr(st, "secrets") else {}
        if isinstance(sec_gov, dict):
            val = sec_gov.get("api_key") or sec_gov.get("GOVTECH_API_KEY")
            if val:
                return val
        if isinstance(sec_open, dict):
            val = sec_open.get("GOVTECH_API_KEY") or sec_open.get("api_key") or sec_open.get("OPENAI_API_KEY")
            if val:
                return val
    except Exception:
        try:
            import os
            if os.getenv("GOVTECH_API_KEY"):
                return os.getenv("GOVTECH_API_KEY")
            if os.getenv("OPENAI_API_KEY"):
                return os.getenv("OPENAI_API_KEY")
        except Exception:
            pass
    return ""
