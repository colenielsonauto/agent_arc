"""
Environment configuration for Email Router.
Loads environment variables from .secrets/.env file.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Optional[str] = None) -> None:
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Optional path to .env file. If None, uses .secrets/.env
    """
    if env_path is None:
        # Get project root (4 levels up from this file)
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        env_path = project_root / ".secrets" / ".env"
    else:
        env_path = Path(env_path)
    
    if not env_path.exists():
        print(f"⚠️  Environment file not found: {env_path}")
        return
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable if not already set
                    if key not in os.environ:
                        os.environ[key] = value
        
        print(f"✅ Environment variables loaded from {env_path}")
        
    except Exception as e:
        print(f"❌ Error loading environment file: {e}")


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get environment variable with optional default and required validation.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: If True, raises ValueError if not found
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValueError: If required=True and variable not found
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' not found")
    
    return value


# Auto-load environment variables when module is imported
load_env_file()


# Common environment variables with defaults
GOOGLE_API_KEY = get_env_var('GOOGLE_API_KEY')
GOOGLE_CLOUD_PROJECT = get_env_var('GOOGLE_CLOUD_PROJECT', 'email-router-460622')
PUBSUB_TOPIC = get_env_var('PUBSUB_TOPIC', f'projects/{GOOGLE_CLOUD_PROJECT}/topics/email-inbound')
ENVIRONMENT = get_env_var('ENVIRONMENT', 'development')
LOG_LEVEL = get_env_var('LOG_LEVEL', 'INFO')
DEBUG_MODE = get_env_var('DEBUG_MODE', 'false').lower() == 'true' 