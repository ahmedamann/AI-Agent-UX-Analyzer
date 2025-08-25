"""
Configuration Manager

This module handles loading, validating, and managing configuration
for the AI Agent UX Analyzer.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigManager:
    """
    Manages configuration loading, validation, and access for the UX Analyzer.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, uses default.
        """
        self.config_path = config_path or "config.yaml"
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from the specified file."""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            logger.debug(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary.
        
        Returns:
            Configuration dictionary
        """
        if self._config is None:
            self._load_config()
        return self._config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'api_keys.openai.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        config = self.get_config()
        keys = key.split('.')
        
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'api_keys.openai.api_key')
            value: Value to set
        """
        config = self.get_config()
        keys = key.split('.')
        
        # Navigate to the parent of the target key
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
    
    def validate_config(self) -> bool:
        """
        Validate the configuration for required fields and values.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            config = self.get_config()
            
            # Check required API keys
            required_keys = [
                'api_keys.openai.api_key',
                'api_keys.anthropic.api_key'
            ]
            
            for key in required_keys:
                if not self.get(key):
                    logger.warning(f"Missing required configuration: {key}")
            
            # Check app store configuration
            if not self.get('app_stores.google_play.enabled') and not self.get('app_stores.app_store.enabled'):
                logger.warning("No app stores are enabled")
            
            # Check clustering configuration
            clustering_config = self.get('clustering', {})
            if not clustering_config.get('algorithm'):
                logger.warning("No clustering algorithm specified")
            
            # Check LLM configuration
            llm_config = self.get('llm_analysis', {})
            if not llm_config.get('provider'):
                logger.warning("No LLM provider specified")
            
            logger.info("Configuration validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Save the current configuration to a file.
        
        Args:
            output_path: Path to save the configuration. If None, uses original path.
        """
        try:
            save_path = output_path or self.config_path
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise
    
    def reload_config(self) -> None:
        """Reload configuration from the file."""
        self._config = None
        self._load_config()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a specific service.
        
        Args:
            service: Service name (e.g., 'openai', 'anthropic', 'google_play')
            
        Returns:
            API key if found, None otherwise
        """
        return self.get(f'api_keys.{service}.api_key')
    
    def get_app_store_config(self, platform: str) -> Dict[str, Any]:
        """
        Get configuration for a specific app store platform.
        
        Args:
            platform: Platform name ('google_play' or 'app_store')
            
        Returns:
            Platform configuration dictionary
        """
        return self.get(f'app_stores.{platform}', {})
    
    def is_platform_enabled(self, platform: str) -> bool:
        """
        Check if a platform is enabled.
        
        Args:
            platform: Platform name ('google_play' or 'app_store')
            
        Returns:
            True if platform is enabled, False otherwise
        """
        return self.get(f'app_stores.{platform}.enabled', False) 