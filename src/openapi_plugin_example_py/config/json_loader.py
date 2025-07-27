"""JSON configuration loader for the application."""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict


def expand_env_vars(value: Any) -> Any:
    """Expand environment variables in configuration values.
    
    Args:
        value: Configuration value (string, dict, list, etc.)
    
    Returns:
        Value with environment variables expanded
    """
    if isinstance(value, str):
        # Replace ${VAR} or $VAR patterns with environment variable values
        def replacer(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        
        # Handle ${VAR} pattern
        value = re.sub(r'\$\{([^}]+)\}', replacer, value)
        # Handle $VAR pattern
        value = re.sub(r'\$([A-Z_][A-Z0-9_]*)', replacer, value)
        return value
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


def load_json_config(environment: str = None) -> Dict[str, Any]:
    """Load configuration from JSON files.
    
    Args:
        environment: Environment name (e.g., 'Development', 'Production')
    
    Returns:
        Merged configuration dictionary with environment variables expanded
    """
    config = {}
    
    # Base configuration file
    base_config_path = Path("appsettings.json")
    if base_config_path.exists():
        with open(base_config_path) as f:
            config = json.load(f)
    
    # Environment-specific configuration
    if environment:
        env_config_path = Path(f"appsettings.{environment}.json")
        if env_config_path.exists():
            with open(env_config_path) as f:
                env_config = json.load(f)
                # Deep merge configurations
                config = deep_merge(config, env_config)
    
    # Expand environment variables
    config = expand_env_vars(config)
    
    return config


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_config(config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    """Flatten nested configuration to environment variable format.
    
    Args:
        config: Configuration dictionary
        prefix: Prefix for keys
    
    Returns:
        Flattened configuration
    """
    result = {}
    
    for key, value in config.items():
        if prefix:
            full_key = f"{prefix}_{key}".upper()
        else:
            full_key = key.upper()
        
        if isinstance(value, dict):
            # Recursively flatten nested dictionaries
            result.update(flatten_config(value, full_key))
        else:
            result[full_key] = value
    
    return result