"""
API Client for Drawing Analysis
Handles communication with OpenAI, GovTech, and other AI providers.
"""
import base64
import json
import os
import requests
from typing import Dict, Any, List, Tuple
from pathlib import Path


class APIClient:
    """Handles API communication for drawing analysis."""
    
    def __init__(self, provider: str = "OpenAI", model: str = "gpt-4o-mini"):
        self.provider = provider
        self.model = model
        self.timeout = 180
        self.max_tokens = 4000
        
    def analyze_with_ai(self, system_prompt: str, user_prompt: str, 
                       image_paths: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Analyze drawings using AI providers."""
        if self.provider == "OpenAI":
            return self._call_openai(system_prompt, user_prompt, image_paths, api_key)
        elif self.provider == "GovTech":
            return self._call_govtech(system_prompt, user_prompt, image_paths, api_key)
        else:
            return False, {"error": f"Unsupported provider: {self.provider}"}
    
    def _call_openai(self, system_prompt: str, user_prompt: str, 
                    image_paths: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Call OpenAI API for drawing analysis."""
        try:
            # Encode images
            images_data = self._encode_images(image_paths)
            if not images_data:
                return False, {"error": "Failed to encode any images"}
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user", 
                    "content": [{"type": "text", "text": user_prompt}] + images_data
                }
            ]
            
            # Make API call
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": self.max_tokens
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"].strip()
            return True, {"content": content}
            
        except requests.exceptions.RequestException as req_err:
            return False, {"error": f"API request failed: {str(req_err)}"}
        except Exception as general_err:
            return False, {"error": f"OpenAI API call failed: {str(general_err)}"}
    
    def _call_govtech(self, system_prompt: str, user_prompt: str, 
                     image_paths: List[str], api_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Call GovTech API for drawing analysis."""
        # Placeholder - GovTech may not support image analysis
        return False, {"error": "GovTech API does not currently support image analysis"}
    
    def _encode_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Encode images to base64 with proper MIME type detection."""
        images_data = []
        
        for img_path in image_paths:
            try:
                # Determine MIME type
                ext = os.path.splitext(img_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    mime_type = "image/jpeg"
                elif ext == '.png':
                    mime_type = "image/png"
                else:
                    print(f"[WARNING] Unknown image type for {img_path}, using jpeg")
                    mime_type = "image/jpeg"
                
                # Encode image
                with open(img_path, 'rb') as file_handle:
                    img_data = base64.b64encode(file_handle.read()).decode('utf-8')
                    images_data.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{img_data}"}
                    })
                    
                print(f"[DEBUG] Successfully encoded {os.path.basename(img_path)} as {mime_type}")
                
            except Exception as exception:
                print(f"[ERROR] Failed to encode {os.path.basename(img_path)}: {exception}")
                continue
        
        print(f"[DEBUG] Successfully encoded {len(images_data)} images")
        return images_data
    
    def save_debug_info(self, system_prompt: str, user_prompt: str, 
                       image_count: int, dxf_count: int) -> None:
        """Save debug information for troubleshooting."""
        debug_info = {
            "timestamp": str(pd.Timestamp.now()),
            "provider": self.provider,
            "model": self.model,
            "image_count": image_count,
            "dxf_count": dxf_count,
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt)
        }
        
        try:
            with open("debug_agent2_prompts.txt", "w", encoding='utf-8') as file_handle:
                file_handle.write("=== AGENT 2 DEBUG INFO ===\n")
                for key, value in debug_info.items():
                    file_handle.write(f"{key.replace('_', ' ').title()}: {value}\n")
                file_handle.write("\n=== SYSTEM PROMPT ===\n")
                file_handle.write(system_prompt)
                file_handle.write("\n\n=== USER PROMPT ===\n")
                file_handle.write(user_prompt)
            print("[DEBUG] Saved debug prompts to debug_agent2_prompts.txt")
        except Exception as exception:
            print(f"[WARNING] Could not save debug prompts: {exception}")
    
    def set_model_config(self, model: str = None, max_tokens: int = None, 
                        timeout: int = None) -> None:
        """Configure model parameters."""
        if model:
            self.model = model
        if max_tokens:
            self.max_tokens = max_tokens  
        if timeout:
            self.timeout = timeout
        
        print(f"[DEBUG] Model config updated: {self.model}, "
              f"max_tokens: {self.max_tokens}, timeout: {self.timeout}")