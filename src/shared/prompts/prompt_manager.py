"""
Prompt management system.

This module provides a centralized system for managing AI prompts,
including versioning, templating, and optimization.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from jinja2 import Template, Environment, FileSystemLoader


@dataclass
class PromptTemplate:
    """A prompt template with metadata."""
    name: str
    content: str
    version: str = "1.0.0"
    description: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def render(self, **kwargs) -> str:
        """Render the prompt with variables."""
        template = Template(self.content)
        return template.render(**kwargs)
    
    def validate_variables(self, variables: Dict[str, Any]) -> bool:
        """Validate that all required variables are provided."""
        return all(var in variables for var in self.variables)


class PromptManager:
    """
    Centralized prompt management system.
    
    This class handles loading, caching, and rendering of prompts
    with support for versioning and A/B testing.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize the prompt manager.
        
        Args:
            prompts_dir: Directory containing prompt files
        """
        if prompts_dir is None:
            # Default to the prompts directory in shared
            current_dir = Path(__file__).parent
            prompts_dir = str(current_dir)
        
        self.prompts_dir = Path(prompts_dir)
        self.templates: Dict[str, PromptTemplate] = {}
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.prompts_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Load all prompts on initialization
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompts from the prompts directory."""
        # Load markdown prompts
        for prompt_file in self.prompts_dir.glob("*.md"):
            self._load_prompt_file(prompt_file)
        
        # Load JSON prompt definitions
        for json_file in self.prompts_dir.glob("*.json"):
            self._load_json_prompts(json_file)
    
    def _load_prompt_file(self, file_path: Path) -> None:
        """Load a single prompt file."""
        try:
            content = file_path.read_text()
            name = file_path.stem
            
            # Extract metadata from frontmatter if present
            metadata = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    try:
                        metadata = yaml.safe_load(parts[1])
                        content = parts[2].strip()
                    except:
                        pass
            
            # Extract variables from template
            template = Template(content)
            variables = list(template.module.__dict__.get('blocks', {}).keys())
            
            # Create prompt template
            prompt = PromptTemplate(
                name=name,
                content=content,
                version=metadata.get("version", "1.0.0"),
                description=metadata.get("description"),
                variables=metadata.get("variables", variables),
                examples=metadata.get("examples", []),
                metadata=metadata,
            )
            
            self.templates[name] = prompt
            
        except Exception as e:
            print(f"Error loading prompt {file_path}: {e}")
    
    def _load_json_prompts(self, file_path: Path) -> None:
        """Load prompts from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                # Single prompt or collection
                if "prompts" in data:
                    # Collection of prompts
                    for prompt_data in data["prompts"]:
                        self._create_prompt_from_dict(prompt_data)
                else:
                    # Single prompt
                    self._create_prompt_from_dict(data)
            
        except Exception as e:
            print(f"Error loading JSON prompts {file_path}: {e}")
    
    def _create_prompt_from_dict(self, data: Dict[str, Any]) -> None:
        """Create a prompt template from dictionary data."""
        prompt = PromptTemplate(
            name=data["name"],
            content=data["content"],
            version=data.get("version", "1.0.0"),
            description=data.get("description"),
            variables=data.get("variables", []),
            examples=data.get("examples", []),
            metadata=data.get("metadata", {}),
        )
        
        self.templates[prompt.name] = prompt
    
    def get_prompt(
        self,
        name: str,
        version: Optional[str] = None,
        **variables
    ) -> str:
        """
        Get a rendered prompt by name.
        
        Args:
            name: Name of the prompt template
            version: Optional specific version
            **variables: Variables to render the prompt with
            
        Returns:
            Rendered prompt string
        """
        if name not in self.templates:
            # Try to load from file if not cached
            file_path = self.prompts_dir / f"{name}.md"
            if file_path.exists():
                self._load_prompt_file(file_path)
            else:
                raise ValueError(f"Prompt '{name}' not found")
        
        template = self.templates[name]
        
        # Validate variables
        if not template.validate_variables(variables):
            missing = set(template.variables) - set(variables.keys())
            raise ValueError(f"Missing required variables: {missing}")
        
        return template.render(**variables)
    
    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template object."""
        if name not in self.templates:
            raise ValueError(f"Prompt '{name}' not found")
        
        return self.templates[name]
    
    def list_prompts(self) -> List[str]:
        """List all available prompt names."""
        return list(self.templates.keys())
    
    def save_prompt(
        self,
        name: str,
        content: str,
        version: str = "1.0.0",
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
        format: str = "md"
    ) -> None:
        """
        Save a new prompt template.
        
        Args:
            name: Name of the prompt
            content: Prompt content
            version: Version string
            description: Optional description
            variables: List of required variables
            examples: Optional examples
            format: File format (md or json)
        """
        template = PromptTemplate(
            name=name,
            content=content,
            version=version,
            description=description,
            variables=variables or [],
            examples=examples or [],
        )
        
        if format == "md":
            # Save as markdown with frontmatter
            file_path = self.prompts_dir / f"{name}.md"
            
            frontmatter = {
                "version": version,
                "description": description,
                "variables": variables,
                "examples": examples,
            }
            
            # Remove None values
            frontmatter = {k: v for k, v in frontmatter.items() if v is not None}
            
            if frontmatter:
                import yaml
                content_with_meta = f"---\n{yaml.dump(frontmatter)}---\n\n{content}"
            else:
                content_with_meta = content
            
            file_path.write_text(content_with_meta)
            
        else:
            # Save as JSON
            file_path = self.prompts_dir / f"{name}.json"
            data = {
                "name": name,
                "content": content,
                "version": version,
                "description": description,
                "variables": variables,
                "examples": examples,
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        # Update cache
        self.templates[name] = template
    
    def optimize_prompt(
        self,
        name: str,
        feedback: List[Dict[str, Any]],
        target_metric: str = "accuracy"
    ) -> str:
        """
        Optimize a prompt based on feedback.
        
        This is a placeholder for future prompt optimization logic
        using techniques like few-shot learning or prompt tuning.
        
        Args:
            name: Name of the prompt to optimize
            feedback: List of feedback examples
            target_metric: Metric to optimize for
            
        Returns:
            Optimized prompt content
        """
        # TODO: Implement prompt optimization
        # For now, just return the original prompt
        return self.get_template(name).content


# Global prompt manager instance
_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager 