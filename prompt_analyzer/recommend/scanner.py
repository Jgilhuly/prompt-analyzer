"""Scanner for existing Cursor rules and commands."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from os.path import expanduser


def get_user_cursor_path() -> Path:
    """Get the user's global Cursor directory path.
    
    Returns:
        Path to ~/.cursor/
    """
    return Path(expanduser("~/.cursor"))


def scan_existing_rules(paths: List[str]) -> List[Dict[str, Any]]:
    """Scan for existing rules from .cursor/rules directories.
    
    Rules are stored in .cursor/rules/{name}/RULE.md files.
    For user global: ~/.cursor/rules/{name}/RULE.md
    For projects: {project}/.cursor/rules/{name}/RULE.md
    
    Args:
        paths: List of base paths to scan (e.g., ['~/.cursor', '/path/to/project'])
        
    Returns:
        List of rule dictionaries with keys: name, content, source_path, scope
    """
    rules = []
    user_cursor_path = get_user_cursor_path()
    
    for base_path_str in paths:
        base_path = Path(expanduser(base_path_str)) if base_path_str.startswith('~') else Path(base_path_str)
        
        # Determine scope and rules directory path
        if str(base_path) == str(user_cursor_path):
            # User global: ~/.cursor/rules
            scope = 'user'
            rules_dir = base_path / 'rules'
        else:
            # Project: {project}/.cursor/rules
            scope = 'project'
            rules_dir = base_path / '.cursor' / 'rules'
        
        if not rules_dir.exists():
            continue
        
        # Scan for rule directories
        for rule_dir in rules_dir.iterdir():
            if not rule_dir.is_dir():
                continue
            
            rule_file = rule_dir / 'RULE.md'
            if rule_file.exists():
                try:
                    content = rule_file.read_text(encoding='utf-8')
                    name = rule_dir.name
                    
                    rules.append({
                        'name': name,
                        'content': content,
                        'source_path': str(base_path),
                        'scope': scope,
                        'type': 'rule',
                    })
                except Exception as e:
                    # Skip files that can't be read
                    continue
    
    return rules


def scan_existing_commands(paths: List[str]) -> List[Dict[str, Any]]:
    """Scan for existing commands from .cursor/commands directories.
    
    Commands are stored as .cursor/commands/{name}.md files.
    For user global: ~/.cursor/commands/{name}.md
    For projects: {project}/.cursor/commands/{name}.md
    
    Args:
        paths: List of base paths to scan (e.g., ['~/.cursor', '/path/to/project'])
        
    Returns:
        List of command dictionaries with keys: name, content, source_path, scope
    """
    commands = []
    user_cursor_path = get_user_cursor_path()
    
    for base_path_str in paths:
        base_path = Path(expanduser(base_path_str)) if base_path_str.startswith('~') else Path(base_path_str)
        
        # Determine scope and commands directory path
        if str(base_path) == str(user_cursor_path):
            # User global: ~/.cursor/commands
            scope = 'user'
            commands_dir = base_path / 'commands'
        else:
            # Project: {project}/.cursor/commands
            scope = 'project'
            commands_dir = base_path / '.cursor' / 'commands'
        
        if not commands_dir.exists():
            continue
        
        # Scan for command files
        for cmd_file in commands_dir.glob('*.md'):
            try:
                content = cmd_file.read_text(encoding='utf-8')
                name = cmd_file.stem  # filename without .md extension
                
                commands.append({
                    'name': name,
                    'content': content,
                    'source_path': str(base_path),
                    'scope': scope,
                    'type': 'command',
                })
            except Exception as e:
                # Skip files that can't be read
                continue
    
    return commands


def scan_all_existing(
    project_paths: Optional[List[str]] = None,
    include_cwd: bool = True,
) -> Dict[str, List[Dict[str, Any]]]:
    """Scan for all existing rules and commands.
    
    Args:
        project_paths: Optional list of project paths to scan
        include_cwd: Whether to include current working directory
        
    Returns:
        Dictionary with 'rules' and 'commands' keys, each containing lists
    """
    paths_to_scan = []
    
    # Always include user global directory
    user_cursor = get_user_cursor_path()
    paths_to_scan.append(str(user_cursor))
    
    # Include current working directory if requested
    if include_cwd:
        cwd = Path.cwd()
        paths_to_scan.append(str(cwd))
    
    # Include project paths
    if project_paths:
        for project_path in project_paths:
            if project_path and project_path not in paths_to_scan:
                paths_to_scan.append(project_path)
    
    rules = scan_existing_rules(paths_to_scan)
    commands = scan_existing_commands(paths_to_scan)
    
    return {
        'rules': rules,
        'commands': commands,
    }

