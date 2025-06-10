"""
Client configuration loader with YAML validation and caching.
📁 Loads and validates client configurations from YAML files.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, List
from functools import lru_cache
import yaml
from pydantic import ValidationError

from ..models.client_config import (
    ClientConfig, 
    RoutingRules, 
    CategoriesConfig, 
    SLAConfig
)

logger = logging.getLogger(__name__)

# Cache for loaded configurations
_config_cache: Dict[str, Dict] = {}
_file_timestamps: Dict[str, float] = {}

# Base path for client configurations
CLIENTS_BASE_PATH = Path("clients/active")


class ClientLoadError(Exception):
    """Exception raised when client loading fails."""
    pass


def get_available_clients() -> List[str]:
    """
    Get list of available client IDs.
    
    Returns:
        List of client IDs (directory names)
    """
    if not CLIENTS_BASE_PATH.exists():
        logger.warning(f"Clients directory not found: {CLIENTS_BASE_PATH}")
        return []
    
    clients = []
    for client_dir in CLIENTS_BASE_PATH.iterdir():
        if client_dir.is_dir() and client_dir.name.startswith('client-'):
            clients.append(client_dir.name)
    
    logger.info(f"Found {len(clients)} available clients: {clients}")
    return clients


def _load_yaml_file(file_path: Path) -> Dict:
    """
    Load and parse a YAML file.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Parsed YAML data as dictionary
        
    Raises:
        ClientLoadError: If file cannot be loaded or parsed
    """
    try:
        if not file_path.exists():
            raise ClientLoadError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if data is None:
            raise ClientLoadError(f"Empty or invalid YAML file: {file_path}")
        
        logger.debug(f"Loaded YAML file: {file_path}")
        return data
        
    except yaml.YAMLError as e:
        raise ClientLoadError(f"YAML parsing error in {file_path}: {e}")
    except Exception as e:
        raise ClientLoadError(f"Error loading {file_path}: {e}")


def _check_file_modified(file_path: Path) -> bool:
    """
    Check if file has been modified since last load.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if file has been modified
    """
    if not file_path.exists():
        return True
    
    current_mtime = file_path.stat().st_mtime
    cached_mtime = _file_timestamps.get(str(file_path))
    
    if cached_mtime is None or current_mtime > cached_mtime:
        _file_timestamps[str(file_path)] = current_mtime
        return True
    
    return False


def load_client_config(client_id: str, force_reload: bool = False) -> ClientConfig:
    """
    Load and validate client configuration.
    
    Args:
        client_id: Client identifier (e.g., 'client-001-acme-corp')
        force_reload: Force reload from disk, ignoring cache
        
    Returns:
        Validated ClientConfig object
        
    Raises:
        ClientLoadError: If configuration cannot be loaded or is invalid
    """
    client_path = CLIENTS_BASE_PATH / client_id
    config_file = client_path / "client-config.yaml"
    
    # Check cache first (unless force reload)
    cache_key = f"{client_id}_config"
    if not force_reload and cache_key in _config_cache:
        if not _check_file_modified(config_file):
            logger.debug(f"Using cached client config for {client_id}")
            return _config_cache[cache_key]
    
    try:
        # Load YAML data
        config_data = _load_yaml_file(config_file)
        
        # Validate with pydantic
        client_config = ClientConfig(**config_data)
        
        # Cache the validated config
        _config_cache[cache_key] = client_config
        logger.info(f"Loaded client config for {client_id}")
        
        return client_config
        
    except ValidationError as e:
        error_msg = f"Invalid client configuration for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)
    except Exception as e:
        error_msg = f"Failed to load client config for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)


def load_routing_rules(client_id: str, force_reload: bool = False) -> RoutingRules:
    """
    Load and validate routing rules configuration.
    
    Args:
        client_id: Client identifier
        force_reload: Force reload from disk, ignoring cache
        
    Returns:
        Validated RoutingRules object
        
    Raises:
        ClientLoadError: If configuration cannot be loaded or is invalid
    """
    client_path = CLIENTS_BASE_PATH / client_id
    routing_file = client_path / "routing-rules.yaml"
    
    # Check cache first
    cache_key = f"{client_id}_routing"
    if not force_reload and cache_key in _config_cache:
        if not _check_file_modified(routing_file):
            logger.debug(f"Using cached routing rules for {client_id}")
            return _config_cache[cache_key]
    
    try:
        # Load YAML data
        routing_data = _load_yaml_file(routing_file)
        
        # Validate with pydantic
        routing_rules = RoutingRules(**routing_data)
        
        # Cache the validated config
        _config_cache[cache_key] = routing_rules
        logger.info(f"Loaded routing rules for {client_id}")
        
        return routing_rules
        
    except ValidationError as e:
        error_msg = f"Invalid routing rules for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)
    except Exception as e:
        error_msg = f"Failed to load routing rules for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)


def load_ai_prompt(client_id: str, prompt_type: str) -> str:
    """
    Load AI prompt template for a client.
    
    Args:
        client_id: Client identifier
        prompt_type: Type of prompt ('classification', 'acknowledgment', 'team-analysis')
        
    Returns:
        Prompt template content as string
        
    Raises:
        ClientLoadError: If prompt cannot be loaded
    """
    client_path = CLIENTS_BASE_PATH / client_id
    prompt_file = client_path / "ai-context" / f"{prompt_type}-prompt.md"
    
    try:
        if not prompt_file.exists():
            raise ClientLoadError(f"AI prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.debug(f"Loaded AI prompt {prompt_type} for {client_id}")
        return content
        
    except Exception as e:
        error_msg = f"Failed to load AI prompt {prompt_type} for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)


def load_fallback_responses(client_id: str) -> Dict:
    """
    Load fallback responses configuration.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Fallback responses as dictionary
        
    Raises:
        ClientLoadError: If fallback responses cannot be loaded
    """
    client_path = CLIENTS_BASE_PATH / client_id
    fallback_file = client_path / "ai-context" / "fallback-responses.yaml"
    
    try:
        fallback_data = _load_yaml_file(fallback_file)
        logger.debug(f"Loaded fallback responses for {client_id}")
        return fallback_data
        
    except Exception as e:
        error_msg = f"Failed to load fallback responses for {client_id}: {e}"
        logger.error(error_msg)
        raise ClientLoadError(error_msg)


def clear_cache(client_id: Optional[str] = None):
    """
    Clear configuration cache.
    
    Args:
        client_id: If provided, clear cache only for this client.
                  If None, clear entire cache.
    """
    global _config_cache, _file_timestamps
    
    if client_id:
        # Clear cache for specific client
        keys_to_remove = [k for k in _config_cache.keys() if k.startswith(f"{client_id}_")]
        for key in keys_to_remove:
            _config_cache.pop(key, None)
        logger.info(f"Cleared cache for client {client_id}")
    else:
        # Clear entire cache
        _config_cache.clear()
        _file_timestamps.clear()
        logger.info("Cleared entire configuration cache") 