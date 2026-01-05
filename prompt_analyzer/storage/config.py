"""Config management."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .paths import get_config_path


class Config:
    """Configuration manager for cursor-prompts."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager."""
        self.config_path = config_path or get_config_path()
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                self._config = json.load(f)
        else:
            self._config = self._default_config()
        return self._config.copy()

    def save(self, config: Optional[Dict[str, Any]] = None):
        """Save configuration to file."""
        if config is not None:
            self._config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        if not self._config:
            self.load()
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value."""
        if not self._config:
            self.load()
        self._config[key] = value
        self.save()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        from pathlib import Path
        storage_dir = Path.home() / ".prompt-analyzer"
        return {
            "storage_path": str(storage_dir / "data" / "prompts.db"),
            "version": "1.0.0",
        }

