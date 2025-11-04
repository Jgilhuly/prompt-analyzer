"""Hook setup and installation."""

import json
import os
from pathlib import Path
from typing import Optional

from .generator import generate_hook_script, get_hooks_json_content


def get_cursor_hooks_dir() -> Path:
    """Get the Cursor hooks directory (~/.cursor)."""
    return Path.home() / ".cursor"


def get_hooks_json_path() -> Path:
    """Get the hooks.json path (~/.cursor/hooks.json)."""
    return get_cursor_hooks_dir() / "hooks.json"


def get_hook_script_path() -> Path:
    """Get the hook script path (~/.cursor/hooks/prompt-analyzer.js)."""
    hooks_dir = get_cursor_hooks_dir() / "hooks"
    return hooks_dir / "prompt-analyzer.js"


def install_hooks(
    storage_path: Optional[Path] = None,
    hooks_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> tuple[bool, str]:
    """Install hooks configuration and script.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        cursor_dir = get_cursor_hooks_dir()
        hooks_json_path = get_hooks_json_path()
        hook_script_path = get_hook_script_path()
        
        # Create hooks directory if needed
        hook_script_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if hooks.json already exists
        hooks_json_exists = hooks_json_path.exists()
        hook_script_exists = hook_script_path.exists()
        
        if hooks_json_exists and not overwrite:
            # Read existing hooks.json and merge
            try:
                with open(hooks_json_path, 'r') as f:
                    existing_hooks = json.load(f)
            except json.JSONDecodeError:
                existing_hooks = {"hooks": []}
        else:
            existing_hooks = {"hooks": []}
        
        # Check if our hook is already registered
        hook_already_registered = any(
            hook.get("hook") == str(hook_script_path)
            for hook in existing_hooks.get("hooks", [])
        )
        
        if hook_already_registered and not overwrite:
            return False, f"Hook already registered in {hooks_json_path}. Use --overwrite to replace."
        
        # Generate hook script
        hook_script_content = generate_hook_script(storage_path)
        
        # Write hook script
        with open(hook_script_path, 'w') as f:
            f.write(hook_script_content)
        
        # Make script executable
        os.chmod(hook_script_path, 0o755)
        
        # Update hooks.json
        if overwrite or not hook_already_registered:
            new_hooks_config = get_hooks_json_content(hook_script_path)
            
            if not overwrite and hooks_json_exists:
                # Merge with existing hooks
                existing_hooks_list = existing_hooks.get("hooks", [])
                # Remove old prompt-analyzer hook if it exists
                existing_hooks_list = [
                    h for h in existing_hooks_list
                    if str(hook_script_path) not in str(h.get("hook", ""))
                ]
                existing_hooks_list.extend(new_hooks_config["hooks"])
                existing_hooks["hooks"] = existing_hooks_list
            else:
                existing_hooks = new_hooks_config
            
            with open(hooks_json_path, 'w') as f:
                json.dump(existing_hooks, f, indent=2)
        
        return True, f"Hooks installed successfully:\n  - {hook_script_path}\n  - {hooks_json_path}"
    
    except Exception as e:
        return False, f"Failed to install hooks: {str(e)}"


def uninstall_hooks() -> tuple[bool, str]:
    """Uninstall hooks configuration and script.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        hooks_json_path = get_hooks_json_path()
        hook_script_path = get_hook_script_path()
        
        # Remove hook script
        if hook_script_path.exists():
            hook_script_path.unlink()
        
        # Remove hook from hooks.json
        if hooks_json_path.exists():
            try:
                with open(hooks_json_path, 'r') as f:
                    hooks_config = json.load(f)
                
                # Remove prompt-analyzer hooks
                hooks_config["hooks"] = [
                    h for h in hooks_config.get("hooks", [])
                    if str(hook_script_path) not in str(h.get("hook", ""))
                ]
                
                # Write back (or remove file if no hooks left)
                if hooks_config.get("hooks"):
                    with open(hooks_json_path, 'w') as f:
                        json.dump(hooks_config, f, indent=2)
                else:
                    hooks_json_path.unlink()
                
            except json.JSONDecodeError:
                # Invalid JSON, just remove it
                hooks_json_path.unlink()
        
        return True, "Hooks uninstalled successfully"
    
    except Exception as e:
        return False, f"Failed to uninstall hooks: {str(e)}"

