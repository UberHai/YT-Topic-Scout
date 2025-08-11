"""Configuration management for YouTube Topic-Scout."""
import json
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Centralized configuration management."""
    
    def __init__(self, config_path: str = "config.json"):
        # Determine the project root directory (YT Topic-Scout)
        project_root = Path(__file__).resolve().parent.parent.parent
        
        # Create an absolute path to the config file
        config_file = project_root / config_path
        
        self.config_path = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        config = {}
        
        # Load from config file
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config.update(json.load(f))
        
        # Override with environment variables
        for key, value in os.environ.items():
            if key.startswith('YOUTUBE_') or key.startswith('API_'):
                config[key] = value
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback."""
        return self._config.get(key, default)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = str(self.get(key, default)).lower()
        return value in ('true', '1', 'yes', 'on')

# Global config instance
config = Config()

# Constants for backward compatibility
MAX_RESULTS = config.get_int('MAX_RESULTS', 10)
BATCH_SIZE = config.get_int('BATCH_SIZE', 50)
CACHE_TTL = config.get_int('CACHE_TTL', 3600)
API_RETRY_ATTEMPTS = config.get_int('API_RETRY_ATTEMPTS', 3)
API_RETRY_DELAY = config.get_int('API_RETRY_DELAY', 1)
DB_TIMEOUT = config.get_int('DB_TIMEOUT', 30)
MAX_VIDEOS_RETAINED = config.get_int('MAX_VIDEOS_RETAINED', 1000)
