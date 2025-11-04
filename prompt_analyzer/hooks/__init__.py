"""Hook script generator and templates module."""

from .generator import generate_hook_script, get_hooks_json_content
from .installer import install_hooks, uninstall_hooks, get_hooks_json_path, get_hook_script_path

__all__ = [
    "generate_hook_script",
    "get_hooks_json_content",
    "install_hooks",
    "uninstall_hooks",
    "get_hooks_json_path",
    "get_hook_script_path",
]

