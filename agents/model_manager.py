"""
Dynamic Model Manager for AECOA
Handles detection and management of available AI models across providers
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import streamlit as st
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about an AI model"""
    name: str
    provider: str
    description: str
    context_length: int
    supports_vision: bool
    cost_per_1k_tokens: Optional[float] = None
    recommended_for: List[str] = None

class ModelManager:
    """Manages available AI models across all providers"""
    
    def __init__(self):
        self.models_cache = {}
        self.cache_duration = 300  # 5 minutes
        self.last_update = {}
        
    # Latest OpenAI Models (as of September 2024)
    OPENAI_MODELS = {
        # GPT-5 Series (Next Generation)
        "gpt-5-main": ModelInfo(
            name="gpt-5-main",
            provider="OpenAI",
            description="GPT-5 main model - most advanced AI",
            context_length=200000,
            supports_vision=True,
            cost_per_1k_tokens=0.020,
            recommended_for=["advanced compliance analysis", "complex reasoning", "regulatory interpretation"]
        ),
        "gpt-5-main-mini": ModelInfo(
            name="gpt-5-main-mini",
            provider="OpenAI",
            description="GPT-5 mini - efficient next-gen model",
            context_length=200000,
            supports_vision=True,
            cost_per_1k_tokens=0.008,
            recommended_for=["cost-effective advanced analysis", "high-volume processing", "general tasks"]
        ),
        "gpt-5-thinking": ModelInfo(
            name="gpt-5-thinking",
            provider="OpenAI",
            description="GPT-5 thinking model - enhanced reasoning",
            context_length=200000,
            supports_vision=False,
            cost_per_1k_tokens=0.025,
            recommended_for=["complex problem solving", "regulatory compliance", "deep analysis"]
        ),
        "gpt-5-thinking-mini": ModelInfo(
            name="gpt-5-thinking-mini",
            provider="OpenAI",
            description="GPT-5 thinking mini - efficient reasoning",
            context_length=200000,
            supports_vision=False,
            cost_per_1k_tokens=0.010,
            recommended_for=["logical analysis", "cost-effective reasoning", "rule interpretation"]
        ),
        
        # GPT-4.1 Series (Enhanced GPT-4)
        "gpt-4.1": ModelInfo(
            name="gpt-4.1",
            provider="OpenAI",
            description="GPT-4.1 enhanced model with improved capabilities",
            context_length=128000,
            supports_vision=True,
            cost_per_1k_tokens=0.012,
            recommended_for=["document analysis", "compliance checking", "multimodal tasks"]
        ),
        "gpt-4.1-mini": ModelInfo(
            name="gpt-4.1-mini",
            provider="OpenAI",
            description="GPT-4.1 mini - compact enhanced model",
            context_length=128000,
            supports_vision=True,
            cost_per_1k_tokens=0.004,
            recommended_for=["efficient processing", "budget-conscious analysis", "routine checks"]
        ),
        
        # GPT-4o Series (Current Generation)
        "gpt-4o": ModelInfo(
            name="gpt-4o",
            provider="OpenAI", 
            description="GPT-4o - most capable current model, multimodal",
            context_length=128000,
            supports_vision=True,
            cost_per_1k_tokens=0.005,
            recommended_for=["compliance analysis", "complex reasoning", "document analysis"]
        ),
        "gpt-4o-mini": ModelInfo(
            name="gpt-4o-mini",
            provider="OpenAI",
            description="GPT-4o mini - fast, cost-effective model",
            context_length=128000,
            supports_vision=True,
            cost_per_1k_tokens=0.00015,
            recommended_for=["quick analysis", "cost optimization", "high-volume processing"]
        ),
        
        # o1 Series (Advanced Reasoning) - keeping for compatibility
        "o1-preview": ModelInfo(
            name="o1-preview",
            provider="OpenAI",
            description="o1 preview - advanced reasoning model",
            context_length=128000,
            supports_vision=False,
            cost_per_1k_tokens=0.015,
            recommended_for=["complex problem solving", "regulatory analysis", "compliance reasoning"]
        ),
        "o1-mini": ModelInfo(
            name="o1-mini",
            provider="OpenAI",
            description="o1 mini - faster reasoning model",
            context_length=128000,
            supports_vision=False,
            cost_per_1k_tokens=0.003,
            recommended_for=["logical analysis", "rule interpretation", "faster reasoning"]
        ),
        
        # GPT-4 Turbo - keeping for compatibility
        "gpt-4-turbo": ModelInfo(
            name="gpt-4-turbo",
            provider="OpenAI",
            description="GPT-4 Turbo - high-performance model with vision",
            context_length=128000,
            supports_vision=True,
            cost_per_1k_tokens=0.01,
            recommended_for=["document analysis", "image processing", "comprehensive tasks"]
        ),
        
        # GPT-3.5 Turbo - keeping for compatibility
        "gpt-3.5-turbo": ModelInfo(
            name="gpt-3.5-turbo",
            provider="OpenAI",
            description="GPT-3.5 Turbo - fast and cost-effective",
            context_length=16385,
            supports_vision=False,
            cost_per_1k_tokens=0.0005,
            recommended_for=["basic analysis", "text processing", "budget-friendly options"]
        )
    }
    
    def get_openai_models(self, api_key: str = None) -> Dict[str, ModelInfo]:
        """Get available OpenAI models"""
        try:
            # Return predefined models with latest available
            return self.OPENAI_MODELS.copy()
        except Exception as e:
            logger.error(f"Error fetching OpenAI models: {e}")
            return {}
    
    def get_govtech_models(self, api_key: str = None) -> Dict[str, ModelInfo]:
        """Get available GovTech models"""
        try:
            # GovTech models - using same model catalog as OpenAI
            govtech_models = {
                # GPT-5 Series via GovTech
                "gpt-5-main": ModelInfo(
                    name="gpt-5-main",
                    provider="GovTech",
                    description="GPT-5 main via GovTech gateway - most advanced",
                    context_length=200000,
                    supports_vision=True,
                    recommended_for=["government compliance", "advanced analysis", "secure processing"]
                ),
                "gpt-5-main-mini": ModelInfo(
                    name="gpt-5-main-mini",
                    provider="GovTech",
                    description="GPT-5 mini via GovTech gateway - efficient",
                    context_length=200000,
                    supports_vision=True,
                    recommended_for=["government compliance", "cost-effective processing", "high-volume tasks"]
                ),
                "gpt-5-thinking": ModelInfo(
                    name="gpt-5-thinking",
                    provider="GovTech",
                    description="GPT-5 thinking via GovTech gateway - enhanced reasoning",
                    context_length=200000,
                    supports_vision=False,
                    recommended_for=["complex regulatory analysis", "compliance reasoning", "secure environment"]
                ),
                "gpt-5-thinking-mini": ModelInfo(
                    name="gpt-5-thinking-mini",
                    provider="GovTech",
                    description="GPT-5 thinking mini via GovTech gateway - efficient reasoning",
                    context_length=200000,
                    supports_vision=False,
                    recommended_for=["logical analysis", "rule interpretation", "government tasks"]
                ),
                
                # GPT-4.1 Series via GovTech
                "gpt-4.1": ModelInfo(
                    name="gpt-4.1",
                    provider="GovTech",
                    description="GPT-4.1 enhanced via GovTech gateway",
                    context_length=128000,
                    supports_vision=True,
                    recommended_for=["government compliance", "document analysis", "secure processing"]
                ),
                "gpt-4.1-mini": ModelInfo(
                    name="gpt-4.1-mini",
                    provider="GovTech",
                    description="GPT-4.1 mini via GovTech gateway",
                    context_length=128000,
                    supports_vision=True,
                    recommended_for=["government compliance", "efficient processing", "routine checks"]
                ),
                
                # GPT-4o Series via GovTech
                "gpt-4o": ModelInfo(
                    name="gpt-4o",
                    provider="GovTech",
                    description="GPT-4o via GovTech gateway",
                    context_length=128000,
                    supports_vision=True,
                    recommended_for=["government compliance", "multimodal analysis", "secure processing"]
                ),
                "gpt-4o-mini": ModelInfo(
                    name="gpt-4o-mini",
                    provider="GovTech",
                    description="GPT-4o mini via GovTech gateway",
                    context_length=128000,
                    supports_vision=True,
                    recommended_for=["government compliance", "cost-effective processing", "high-volume tasks"]
                ),
                
                # Legacy models for compatibility
                "gpt-4": ModelInfo(
                    name="gpt-4",
                    provider="GovTech",
                    description="GPT-4 via GovTech gateway",
                    context_length=8192,
                    supports_vision=False,
                    recommended_for=["government compliance", "regulatory analysis", "secure processing"]
                ),
                "gpt-3.5-turbo": ModelInfo(
                    name="gpt-3.5-turbo",
                    provider="GovTech",
                    description="GPT-3.5 Turbo via GovTech gateway",
                    context_length=16385,
                    supports_vision=False,
                    recommended_for=["government compliance", "cost-effective processing", "secure environment"]
                )
            }
            
            # Try to fetch actual available models if API key provided
            if api_key:
                try:
                    headers = {
                        "api-key": api_key,
                        "Content-Type": "application/json"
                    }
                    response = requests.get(
                        "https://llmaas.govtext.gov.sg/gateway/openai/models",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        models_data = response.json()
                        # Process actual available models
                        for model_data in models_data.get('data', []):
                            model_id = model_data.get('id', '')
                            if model_id and model_id not in govtech_models:
                                govtech_models[model_id] = ModelInfo(
                                    name=model_id,
                                    provider="GovTech",
                                    description=f"{model_id} via GovTech gateway",
                                    context_length=8192,  # Default
                                    supports_vision=False,
                                    recommended_for=["government compliance", "secure processing"]
                                )
                except Exception as e:
                    logger.warning(f"Could not fetch live GovTech models: {e}")
            
            return govtech_models
        except Exception as e:
            logger.error(f"Error getting GovTech models: {e}")
            return {}
    
    def get_ollama_models(self, host: str = "http://localhost:11434") -> Dict[str, ModelInfo]:
        """Detect available Ollama models dynamically"""
        ollama_models = {}
        
        # Method 1: Try API detection first
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                for model_data in data.get('models', []):
                    model_name = model_data.get('name', '')
                    if model_name:
                        ollama_models[model_name] = self._create_ollama_model_info(model_name)
        except Exception as e:
            logger.warning(f"Could not detect Ollama models via API: {e}")
        
        # Method 2: Check local installation directory
        ollama_models_path = r"C:\Users\young\.ollama\models"
        try:
            if os.path.exists(ollama_models_path):
                # Check manifests directory for installed models
                manifests_path = os.path.join(ollama_models_path, "manifests", "registry.ollama.ai", "library")
                if os.path.exists(manifests_path):
                    for model_dir in os.listdir(manifests_path):
                        model_path = os.path.join(manifests_path, model_dir)
                        if os.path.isdir(model_path):
                            # Check for version files
                            for version_file in os.listdir(model_path):
                                if version_file != "latest":  # Skip 'latest' symlink
                                    model_name = f"{model_dir}:{version_file}"
                                    if model_name not in ollama_models:
                                        ollama_models[model_name] = self._create_ollama_model_info(model_name)
                                    
                                # Also add the base model name
                                base_model = f"{model_dir}:latest"
                                if base_model not in ollama_models:
                                    ollama_models[base_model] = self._create_ollama_model_info(base_model)
        except Exception as e:
            logger.warning(f"Could not scan local Ollama directory: {e}")
        
        # Method 3: Fallback to common models if nothing found
        if not ollama_models:
            logger.info("Using fallback Ollama models")
            ollama_models = {
                "llama3.2:latest": self._create_ollama_model_info("llama3.2:latest"),
                "llava:latest": self._create_ollama_model_info("llava:latest"),
                "codellama:latest": self._create_ollama_model_info("codellama:latest"),
                "mistral:latest": self._create_ollama_model_info("mistral:latest")
            }
        
        return ollama_models
    
    def _create_ollama_model_info(self, model_name: str) -> ModelInfo:
        """Create ModelInfo for an Ollama model"""
        # Determine model capabilities based on name
        supports_vision = any(keyword in model_name.lower() 
                            for keyword in ['llava', 'vision', 'multimodal'])
        
        # Determine recommended use cases
        recommended = ["local processing", "privacy-focused", "offline capable"]
        if supports_vision:
            recommended.extend(["image analysis", "document processing"])
        if any(keyword in model_name.lower() for keyword in ['code', 'coder']):
            recommended.append("code analysis")
        if "instruct" in model_name.lower():
            recommended.append("instruction following")
        
        return ModelInfo(
            name=model_name,
            provider="Ollama",
            description=f"Local {model_name} model",
            context_length=self._estimate_context_length(model_name),
            supports_vision=supports_vision,
            cost_per_1k_tokens=0.0,  # Free!
            recommended_for=recommended
        )
    
    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length based on model name"""
        model_lower = model_name.lower()
        if any(keyword in model_lower for keyword in ['llama3.2', 'llama-3.2']):
            return 128000
        elif any(keyword in model_lower for keyword in ['llama3.1', 'llama-3.1']):
            return 128000
        elif any(keyword in model_lower for keyword in ['llama3', 'llama-3']):
            return 8192
        elif 'llava' in model_lower:
            return 4096
        else:
            return 4096  # Conservative default
    
    def get_all_models(self, provider_configs: Dict[str, Dict] = None) -> Dict[str, Dict[str, ModelInfo]]:
        """Get all available models from all providers"""
        all_models = {}
        
        provider_configs = provider_configs or {}
        
        # Get OpenAI models
        openai_config = provider_configs.get('openai', {})
        openai_key = openai_config.get('api_key')
        all_models['OpenAI'] = self.get_openai_models(openai_key)
        
        # Get GovTech models
        govtech_config = provider_configs.get('govtech', {})
        govtech_key = govtech_config.get('api_key')
        all_models['GovTech'] = self.get_govtech_models(govtech_key)
        
        # Get Ollama models
        ollama_config = provider_configs.get('ollama', {})
        ollama_host = ollama_config.get('host', 'http://localhost:11434')
        all_models['Ollama'] = self.get_ollama_models(ollama_host)
        
        return all_models
    
    def get_recommended_model(self, task_type: str, provider: str = None) -> Optional[ModelInfo]:
        """Get recommended model for a specific task type"""
        task_recommendations = {
            "compliance_analysis": ["o1-preview", "gpt-4o", "gpt-4-turbo"],
            "document_processing": ["gpt-4o", "gpt-4-turbo", "llava:latest"],
            "cost_optimization": ["gpt-4o-mini", "gpt-3.5-turbo", "llama3.2:latest"],
            "image_analysis": ["gpt-4o", "gpt-4-turbo", "llava:latest"],
            "fast_processing": ["gpt-4o-mini", "gpt-3.5-turbo", "llama3.2:latest"],
            "privacy_focused": ["llama3.2:latest", "llava:latest"]
        }
        
        recommended_models = task_recommendations.get(task_type, [])
        all_models = self.get_all_models()
        
        # Find first available recommended model
        for model_name in recommended_models:
            for provider_name, models in all_models.items():
                if provider and provider_name != provider:
                    continue
                if model_name in models:
                    return models[model_name]
        
        return None
    
    def get_model_info(self, provider: str, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model"""
        all_models = self.get_all_models()
        provider_models = all_models.get(provider, {})
        return provider_models.get(model_name)

# Global instance
model_manager = ModelManager()