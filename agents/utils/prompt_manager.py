"""
Prompt Management Utility
Handles loading and managing AI prompts from external files.
"""
from typing import Dict
from pathlib import Path

class PromptManager:
    """Manages AI prompts loaded from external files."""
    
    def __init__(self, prompts_dir: str = None):
        """Initialize prompt manager with prompts directory."""
        if prompts_dir is None:
            # Default to prompts folder in project root
            self.prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._prompt_cache = {}
    
    def load_prompt(self, prompt_file: str, **kwargs) -> str:
        """
        Load a prompt from file and optionally format with provided kwargs.
        
        Args:
            prompt_file: Name of the prompt file (e.g., 'agent2_system_prompt.txt')
            **kwargs: Variables to substitute in the prompt template
            
        Returns:
            str: The loaded and formatted prompt
        """
        prompt_path = self.prompts_dir / prompt_file
        
        # Cache prompts to avoid repeated file reads
        if prompt_file not in self._prompt_cache:
            try:
                with open(prompt_path, 'r', encoding='utf-8') as file:
                    self._prompt_cache[prompt_file] = file.read()
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}") from exc
            except Exception as exc:
                raise RuntimeError(f"Error reading prompt file {prompt_path}: {str(exc)}") from exc
        
        prompt_template = self._prompt_cache[prompt_file]
        
        # Format with provided variables if any
        if kwargs:
            try:
                return prompt_template.format(**kwargs)
            except KeyError as exc:
                msg = f"Missing required variable for prompt template: {str(exc)}"
                raise ValueError(msg) from exc
        
        return prompt_template
    
    def load_agent_prompts(self, agent_name: str, **kwargs) -> Dict[str, str]:
        """
        Load system and user prompts for a specific agent.
        
        Args:
            agent_name: Agent identifier (e.g., 'agent2', 'agent3')
            **kwargs: Variables to substitute in prompt templates
            
        Returns:
            Dict[str, str]: Dictionary with 'system' and 'user' prompts
        """
        system_file = f"{agent_name}_system_prompt.txt"
        user_file = f"{agent_name}_user_prompt.txt"
        
        return {
            "system": self.load_prompt(system_file, **kwargs),
            "user": self.load_prompt(user_file, **kwargs)
        }
    
    def list_available_prompts(self) -> list:
        """List all available prompt files."""
        if not self.prompts_dir.exists():
            return []
        
        return [f.name for f in self.prompts_dir.glob("*.txt")]
    
    def clear_cache(self):
        """Clear the prompt cache to force reload from files."""
        self._prompt_cache.clear()

# Global instance for easy access
prompt_manager = PromptManager()

def load_prompt(prompt_file: str, **kwargs) -> str:
    """Convenience function to load a prompt using the global prompt manager."""
    return prompt_manager.load_prompt(prompt_file, **kwargs)

def load_agent_prompts(agent_name: str, **kwargs) -> Dict[str, str]:
    """Convenience function to load agent prompts using the global prompt manager."""
    return prompt_manager.load_agent_prompts(agent_name, **kwargs)