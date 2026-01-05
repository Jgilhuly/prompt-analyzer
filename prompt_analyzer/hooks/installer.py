"""Hook setup and installation."""

import json
import os
import subprocess
import shutil
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
    """Get the hook script path (~/.cursor/hooks/cursor-prompts.js)."""
    hooks_dir = get_cursor_hooks_dir() / "hooks"
    return hooks_dir / "cursor-prompts.js"


def check_and_install_better_sqlite3(hooks_dir: Path) -> tuple[bool, str]:
    """Check if better-sqlite3 is installed locally in hooks directory, and install it if not.
    
    Args:
        hooks_dir: Directory where hooks are installed (~/.cursor/hooks)
    
    Returns:
        (success: bool, message: str)
    """
    # Check if npm is available
    if not shutil.which("npm"):
        return False, "npm not found. Please install Node.js and npm to use cursor-prompts hooks."
    
    # Ensure hooks directory exists
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if better-sqlite3 is installed locally
    node_modules_path = hooks_dir / "node_modules" / "better-sqlite3"
    package_json_path = hooks_dir / "package.json"
    
    if node_modules_path.exists():
        return True, "better-sqlite3 is already installed locally"
    
    # Create package.json if it doesn't exist
    if not package_json_path.exists():
        package_json = {
            "name": "cursor-prompts-hooks",
            "version": "1.0.0",
            "description": "Dependencies for cursor-prompts Cursor hooks",
            "private": True,
            "dependencies": {
                "better-sqlite3": "^11.0.0"
            }
        }
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f, indent=2)
    
    # Install better-sqlite3 locally
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(hooks_dir),
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, "better-sqlite3 installed successfully"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, f"Failed to install better-sqlite3: {error_msg}\nPlease install manually: cd {hooks_dir} && npm install"
    except subprocess.TimeoutExpired:
        return False, f"Installation timed out. Please install manually: cd {hooks_dir} && npm install"
    except Exception as e:
        return False, f"Failed to install better-sqlite3: {str(e)}\nPlease install manually: cd {hooks_dir} && npm install"


def install_hooks(
    storage_path: Optional[Path] = None,
    hooks_dir: Optional[Path] = None,
    overwrite: bool = False,
    check_dependencies: bool = True,
) -> tuple[bool, str]:
    """Install hooks configuration and script.
    
    Args:
        storage_path: Optional custom path for SQLite database
        hooks_dir: Optional custom directory for Cursor hooks
        overwrite: Whether to overwrite existing hooks
        check_dependencies: Whether to check and install Node.js dependencies
    
    Returns:
        (success: bool, message: str)
    """
    try:
        cursor_dir = get_cursor_hooks_dir()
        hooks_json_path = get_hooks_json_path()
        hook_script_path = get_hook_script_path()
        hooks_dir = hook_script_path.parent
        
        # Create hooks directory if needed
        hooks_dir.mkdir(parents=True, exist_ok=True)
        
        # Check and install better-sqlite3 locally if needed
        if check_dependencies:
            success, dep_message = check_and_install_better_sqlite3(hooks_dir)
            if not success:
                return False, dep_message
        
        # Check if hooks.json already exists
        hooks_json_exists = hooks_json_path.exists()
        hook_script_exists = hook_script_path.exists()
        
        if hooks_json_exists and not overwrite:
            # Read existing hooks.json and merge
            try:
                with open(hooks_json_path, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure it's a dict with proper structure
                    if isinstance(loaded_data, dict):
                        existing_hooks = loaded_data
                        # Ensure version exists
                        if "version" not in existing_hooks:
                            existing_hooks["version"] = 1
                        # Ensure hooks key exists and is a dict
                        if "hooks" not in existing_hooks or not isinstance(existing_hooks.get("hooks"), dict):
                            existing_hooks["hooks"] = {}
                    else:
                        existing_hooks = {"version": 1, "hooks": {}}
            except (json.JSONDecodeError, ValueError):
                existing_hooks = {"version": 1, "hooks": {}}
        else:
            existing_hooks = {"version": 1, "hooks": {}}
        
        # Check if our hook is already registered in any hook event
        script_path_str = str(hook_script_path)
        hook_events = [
            "beforeSubmitPrompt",
            "afterAgentResponse"
        ]
        
        hook_already_registered = any(
            event in existing_hooks.get("hooks", {})
            and isinstance(existing_hooks["hooks"][event], list)
            and any(
                isinstance(cmd, dict) and script_path_str in cmd.get("command", "")
                for cmd in existing_hooks["hooks"][event]
            )
            for event in hook_events
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
                # Merge with existing hooks - add our hooks to each event
                for event_name, hook_commands in new_hooks_config["hooks"].items():
                    if event_name not in existing_hooks["hooks"]:
                        existing_hooks["hooks"][event_name] = []
                    elif not isinstance(existing_hooks["hooks"][event_name], list):
                        existing_hooks["hooks"][event_name] = []
                    
                    # Remove any existing cursor-prompts hooks for this event
                    script_path_str = str(hook_script_path)
                    existing_hooks["hooks"][event_name] = [
                        cmd for cmd in existing_hooks["hooks"][event_name]
                        if not (isinstance(cmd, dict) and script_path_str in cmd.get("command", ""))
                    ]
                    
                    # Add our hook commands
                    existing_hooks["hooks"][event_name].extend(hook_commands)
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
        hooks_dir = hook_script_path.parent
        
        # Remove hook script
        if hook_script_path.exists():
            hook_script_path.unlink()
        
        # Optionally remove package.json and node_modules if they exist
        # (only if they were created by cursor-prompts)
        package_json_path = hooks_dir / "package.json"
        node_modules_path = hooks_dir / "node_modules"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    # Only remove if it's our package.json
                    if package_data.get("name") == "cursor-prompts-hooks":
                        package_json_path.unlink()
                        # Remove node_modules if it exists
                        if node_modules_path.exists():
                            shutil.rmtree(node_modules_path)
            except:
                pass  # If we can't read it, leave it alone
        
        # Remove hook from hooks.json
        if hooks_json_path.exists():
            try:
                with open(hooks_json_path, 'r') as f:
                    loaded_data = json.load(f)
                    # Ensure it's a dict with proper structure
                    if isinstance(loaded_data, dict):
                        hooks_config = loaded_data
                        # Ensure hooks key exists and is a dict
                        if "hooks" not in hooks_config or not isinstance(hooks_config.get("hooks"), dict):
                            hooks_config["hooks"] = {}
                    else:
                        hooks_config = {"version": 1, "hooks": {}}
            except (json.JSONDecodeError, ValueError):
                # Invalid JSON, just remove it
                hooks_json_path.unlink()
                return True, "Hooks uninstalled successfully"
            
            # Remove cursor-prompts hooks from all events
            script_path_str = str(hook_script_path)
            for event_name in list(hooks_config.get("hooks", {}).keys()):
                if isinstance(hooks_config["hooks"][event_name], list):
                    hooks_config["hooks"][event_name] = [
                        cmd for cmd in hooks_config["hooks"][event_name]
                        if not (isinstance(cmd, dict) and script_path_str in cmd.get("command", ""))
                    ]
                    # Remove empty event arrays
                    if not hooks_config["hooks"][event_name]:
                        del hooks_config["hooks"][event_name]
            
            # Write back (or remove file if no hooks left)
            if hooks_config.get("hooks"):
                with open(hooks_json_path, 'w') as f:
                    json.dump(hooks_config, f, indent=2)
            else:
                hooks_json_path.unlink()
        
        return True, "Hooks uninstalled successfully"
    
    except Exception as e:
        return False, f"Failed to uninstall hooks: {str(e)}"

