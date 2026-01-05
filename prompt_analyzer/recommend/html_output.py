"""HTML output generator for recommendations."""

import html
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import webbrowser
from urllib.parse import urlencode


def generate_deeplink(type: str, name: str, content: str) -> str:
    """Generate Cursor deeplink URL.
    
    Args:
        type: 'rule' or 'command'
        name: Name of the rule/command
        content: The full content
    
    Returns:
        Deeplink URL (max 8000 chars per Cursor docs)
    """
    base_url = f"cursor://anysphere.cursor-deeplink/{type}"
    params = {"name": name, "text": content}
    query_string = urlencode(params)
    full_url = f"{base_url}?{query_string}"
    
    # Check length limit (8000 chars per Cursor docs)
    if len(full_url) > 8000:
        # Truncate content if needed
        max_content_length = 8000 - len(base_url) - len(urlencode({"name": name, "text": ""}))
        truncated_content = content[:max_content_length]
        params = {"name": name, "text": truncated_content}
        query_string = urlencode(params)
        full_url = f"{base_url}?{query_string}"
    
    return full_url


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor Rules & Commands Recommendations</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background-color: #14120b;
            color: #edecec;
            line-height: 1.6;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: #f54e00;
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }}
        
        .subtitle {{
            color: rgba(237, 236, 236, 0.6);
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }}
        
        /* Tab Styles */
        .tabs {{
            margin-top: 2rem;
        }}
        
        .tab-buttons {{
            display: flex;
            border-bottom: 2px solid #26241e;
            margin-bottom: 2rem;
            gap: 0.5rem;
        }}
        
        .tab-button {{
            background: none;
            border: none;
            color: rgba(237, 236, 236, 0.6);
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            font-size: 0.95rem;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
            transition: color 0.2s;
        }}
        
        .tab-button:hover {{
            color: rgba(237, 236, 236, 0.8);
        }}
        
        .tab-button.active {{
            color: #f54e00;
            border-bottom-color: #f54e00;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            color: #edecec;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #26241e;
        }}
        
        .project-section {{
            margin-bottom: 2rem;
        }}
        
        .project-header {{
            font-size: 1.2rem;
            color: #edecec;
            margin-bottom: 1rem;
            font-weight: 600;
        }}
        
        .recommendation {{
            background-color: #1b1913;
            border: 1px solid #26241e;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        
        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        
        .recommendation-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #edecec;
        }}
        
        .recommendation-type {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .type-rule {{
            background-color: #2b2923;
            color: #f54e00;
        }}
        
        .type-command {{
            background-color: #2b2923;
            color: #edecec;
        }}
        
        .reasoning {{
            color: rgba(237, 236, 236, 0.7);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            font-style: italic;
        }}
        
        .content-block {{
            position: relative;
            background-color: #14120b;
            border: 1px solid #26241e;
            border-radius: 4px;
            padding: 1rem;
            margin-top: 0.5rem;
        }}
        
        .content-code {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
            color: #edecec;
            white-space: pre-wrap;
            word-wrap: break-word;
            margin: 0;
        }}
        
        .button-group {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }}
        
        .copy-button, .deeplink-button {{
            background-color: #26241e;
            color: #edecec;
            border: 1px solid #2b2923;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            font-size: 0.85rem;
            transition: background-color 0.2s;
        }}
        
        .copy-button:hover, .deeplink-button:hover {{
            background-color: #2b2923;
        }}
        
        .copy-button:active, .deeplink-button:active {{
            background-color: #1b1913;
        }}
        
        .copy-button.copied {{
            background-color: #f54e00;
            color: #14120b;
        }}
        
        .deeplink-button {{
            background-color: #f54e00;
            color: #14120b;
            border-color: #f54e00;
        }}
        
        .deeplink-button:hover {{
            background-color: #d94600;
        }}
        
        .instructions {{
            background-color: #1b1913;
            border-left: 3px solid #f54e00;
            padding: 1rem;
            margin-top: 1rem;
            border-radius: 4px;
        }}
        
        .instructions-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #f54e00;
        }}
        
        .instructions-text {{
            color: rgba(237, 236, 236, 0.8);
            font-size: 0.9rem;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: rgba(237, 236, 236, 0.5);
        }}
        
        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        /* Prompt Log Styles */
        .prompt-log {{
            max-height: 600px;
            overflow-y: auto;
        }}
        
        .prompt-entry {{
            background-color: #1b1913;
            border: 1px solid #26241e;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        .prompt-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
            color: rgba(237, 236, 236, 0.6);
        }}
        
        .prompt-text {{
            color: #edecec;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .prompt-action {{
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .action-accepted {{
            background-color: #2b2923;
            color: #4ade80;
        }}
        
        .action-rejected {{
            background-color: #2b2923;
            color: #f87171;
        }}
        
        .action-edited {{
            background-color: #2b2923;
            color: #fbbf24;
        }}
        
        /* Existing Rules/Commands Styles */
        .existing-item {{
            background-color: #1b1913;
            border: 1px solid #26241e;
            border-radius: 4px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        .existing-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        
        .existing-name {{
            font-weight: 600;
            color: #edecec;
        }}
        
        .existing-scope {{
            font-size: 0.75rem;
            color: rgba(237, 236, 236, 0.5);
            text-transform: uppercase;
        }}
        
        .existing-path {{
            font-size: 0.8rem;
            color: rgba(237, 236, 236, 0.5);
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cursor Rules & Commands Recommendations</h1>
        <p class="subtitle">Generated from your recent prompts</p>
        
        <div class="tabs">
            <div class="tab-buttons">
                <button class="tab-button active" data-tab="rules">Rules</button>
                <button class="tab-button" data-tab="commands">Commands</button>
                <button class="tab-button" data-tab="prompt-log">Prompt Log</button>
                <button class="tab-button" data-tab="existing">Existing</button>
            </div>
            
            <div id="rules-tab" class="tab-content active">
                {rules_content}
            </div>
            
            <div id="commands-tab" class="tab-content">
                {commands_content}
            </div>
            
            <div id="prompt-log-tab" class="tab-content">
                {prompt_log_content}
            </div>
            
            <div id="existing-tab" class="tab-content">
                {existing_content}
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName, button) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(function(tab) {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab-button').forEach(function(btn) {{
                btn.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            if (button) {{
                button.classList.add('active');
            }}
        }}
        
        // Set up tab button listeners
        document.querySelectorAll('.tab-button').forEach(function(button) {{
            button.addEventListener('click', function() {{
                const tabName = this.getAttribute('data-tab');
                showTab(tabName, this);
            }});
        }});
        
        function copyToClipboard(text, button) {{
            navigator.clipboard.writeText(text).then(function() {{
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.classList.add('copied');
                setTimeout(function() {{
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }}, 2000);
            }});
        }}
        
        // Set up copy button listeners
        document.querySelectorAll('.copy-button').forEach(function(button) {{
            button.addEventListener('click', function() {{
                const contentBlock = this.closest('.recommendation').querySelector('.content-code');
                copyToClipboard(contentBlock.textContent, this);
            }});
        }});
    </script>
</body>
</html>"""


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(str(text))


def format_recommendation_html(rec: Dict[str, Any], index: int) -> str:
    """Format a single recommendation as HTML with deeplink button.
    
    Args:
        rec: Recommendation dictionary
        index: Index for unique IDs
        
    Returns:
        HTML string for the recommendation
    """
    rec_type = rec.get("type", "Rule").lower()
    name = escape_html(rec.get("name", "Unnamed"))
    content = escape_html(rec.get("content", ""))
    reasoning = escape_html(rec.get("reasoning", ""))
    
    type_class = f"type-{rec_type}"
    type_label = rec_type.capitalize()
    
    # Generate deeplink
    deeplink_url = generate_deeplink(rec_type, name, rec.get("content", ""))
    
    # Determine instructions based on type and scope
    scope = rec.get("scope", "project")
    if scope == "global":
        if rec_type == "rule":
            instructions = "Add this to Cursor Settings → Rules → User Rules"
        else:
            instructions = "Add this to Cursor Settings → Commands → User Commands"
    else:
        safe_name = name.lower().replace(' ', '-').replace('_', '-')
        if rec_type == "rule":
            instructions = f"Create a file at: <code>.cursor/rules/{escape_html(safe_name)}/RULE.md</code>"
        else:
            instructions = f"Create a file at: <code>.cursor/commands/{escape_html(safe_name)}.md</code>"
    
    html_str = f"""
        <div class="recommendation">
            <div class="recommendation-header">
                <div class="recommendation-title">{name}</div>
                <span class="recommendation-type {type_class}">{type_label}</span>
            </div>
            {f'<div class="reasoning">{reasoning}</div>' if reasoning else ''}
            <div class="content-block">
                <pre class="content-code">{content}</pre>
            </div>
            <div class="button-group">
                <button class="copy-button" id="copy-btn-{index}">Copy Content</button>
                <a href="{escape_html(deeplink_url)}" class="deeplink-button" target="_blank">Add to Cursor</a>
            </div>
            <div class="instructions">
                <div class="instructions-title">Where to place:</div>
                <div class="instructions-text">{instructions}</div>
            </div>
        </div>
    """
    
    return html_str


def format_prompt_log_html(prompts: List[Dict[str, Any]]) -> str:
    """Format prompt log as HTML.
    
    Args:
        prompts: List of prompt dictionaries
        
    Returns:
        HTML string for prompt log
    """
    if not prompts:
        return '''
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No prompts found.</p>
            </div>
        '''
    
    parts = ['<div class="prompt-log">']
    
    for prompt in prompts:
        timestamp = prompt.get('timestamp', '')
        prompt_text = prompt.get('prompt_text', '')
        user_action = prompt.get('user_action', '')
        project_path = prompt.get('project_path', '')
        
        # Format timestamp
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = timestamp
        
        # Truncate long prompts
        display_text = prompt_text[:500] + ('...' if len(prompt_text) > 500 else '')
        
        # Action badge
        action_badge = ''
        if user_action:
            action_class = f'action-{user_action}'
            action_badge = f'<span class="prompt-action {action_class}">{escape_html(user_action)}</span>'
        
        parts.append(f'''
            <div class="prompt-entry">
                <div class="prompt-header">
                    <span>{escape_html(formatted_time)}</span>
                    <div>
                        {action_badge}
                        {f'<span style="margin-left: 0.5rem; color: rgba(237, 236, 236, 0.4);">{escape_html(project_path)}</span>' if project_path else ''}
                    </div>
                </div>
                <div class="prompt-text">{escape_html(display_text)}</div>
            </div>
        ''')
    
    parts.append('</div>')
    return '\n'.join(parts)


def format_existing_html(existing: Dict[str, List[Dict[str, Any]]]) -> str:
    """Format existing rules and commands as HTML.
    
    Args:
        existing: Dictionary with 'rules' and 'commands' keys
        
    Returns:
        HTML string for existing items
    """
    rules = existing.get('rules', [])
    commands = existing.get('commands', [])
    
    if not rules and not commands:
        return '''
            <div class="empty-state">
                <div class="empty-state-icon">📁</div>
                <p>No existing rules or commands found.</p>
            </div>
        '''
    
    parts = []
    
    # Group by scope
    user_rules = [r for r in rules if r.get('scope') == 'user']
    project_rules = [r for r in rules if r.get('scope') == 'project']
    user_commands = [c for c in commands if c.get('scope') == 'user']
    project_commands = [c for c in commands if c.get('scope') == 'project']
    
    # User global section
    if user_rules or user_commands:
        parts.append('<div class="section">')
        parts.append('<h2 class="section-title">User Global (~/.cursor/)</h2>')
        
        if user_rules:
            parts.append('<h3 style="font-size: 1.1rem; margin: 1rem 0 0.5rem 0; color: rgba(237, 236, 236, 0.8);">Rules</h3>')
            for rule in user_rules:
                parts.append(format_existing_item_html(rule))
        
        if user_commands:
            parts.append('<h3 style="font-size: 1.1rem; margin: 1rem 0 0.5rem 0; color: rgba(237, 236, 236, 0.8);">Commands</h3>')
            for cmd in user_commands:
                parts.append(format_existing_item_html(cmd))
        
        parts.append('</div>')
    
    # Project-specific section
    if project_rules or project_commands:
        parts.append('<div class="section">')
        parts.append('<h2 class="section-title">Project-Specific</h2>')
        
        # Group by project path
        by_project = {}
        for item in project_rules + project_commands:
            path = item.get('source_path', 'unknown')
            if path not in by_project:
                by_project[path] = {'rules': [], 'commands': []}
            if item.get('type') == 'rule':
                by_project[path]['rules'].append(item)
            else:
                by_project[path]['commands'].append(item)
        
        for project_path, items in by_project.items():
            parts.append(f'<div class="project-section">')
            parts.append(f'<div class="project-header">{escape_html(project_path)}</div>')
            
            if items['rules']:
                parts.append('<h3 style="font-size: 1rem; margin: 0.5rem 0; color: rgba(237, 236, 236, 0.7);">Rules</h3>')
                for rule in items['rules']:
                    parts.append(format_existing_item_html(rule))
            
            if items['commands']:
                parts.append('<h3 style="font-size: 1rem; margin: 0.5rem 0; color: rgba(237, 236, 236, 0.7);">Commands</h3>')
                for cmd in items['commands']:
                    parts.append(format_existing_item_html(cmd))
            
            parts.append('</div>')
        
        parts.append('</div>')
    
    return '\n'.join(parts)


def format_existing_item_html(item: Dict[str, Any]) -> str:
    """Format a single existing rule/command item.
    
    Args:
        item: Dictionary with name, content, source_path, scope, type
        
    Returns:
        HTML string
    """
    name = escape_html(item.get('name', 'Unnamed'))
    content = escape_html(item.get('content', ''))
    source_path = escape_html(item.get('source_path', ''))
    scope = item.get('scope', 'project')
    item_type = item.get('type', 'rule')
    
    # Truncate content for display
    display_content = content[:200] + ('...' if len(content) > 200 else '')
    
    scope_label = 'User Global' if scope == 'user' else 'Project'
    
    # Format path correctly based on scope
    if scope == 'user':
        display_path = f"~/.cursor/{item_type}s/"
    else:
        display_path = f"{source_path}/.cursor/{item_type}s/"
    
    return f'''
        <div class="existing-item">
            <div class="existing-header">
                <div>
                    <div class="existing-name">{name}</div>
                    <div class="existing-scope">{scope_label}</div>
                </div>
                <span class="recommendation-type type-{item_type}">{item_type.capitalize()}</span>
            </div>
            <div class="existing-path">{display_path}</div>
            <div class="content-block" style="margin-top: 0.5rem;">
                <pre class="content-code">{display_content}</pre>
            </div>
        </div>
    '''


def generate_html(
    global_recommendations: List[Dict[str, Any]],
    project_recommendations: Dict[str, List[Dict[str, Any]]],
    prompts: Optional[List[Dict[str, Any]]] = None,
    existing: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> str:
    """Generate HTML page from recommendations with tabs.
    
    Args:
        global_recommendations: List of global recommendations
        project_recommendations: Dictionary mapping project_path to recommendations
        prompts: Optional list of prompts for the log view
        existing: Optional dictionary with 'rules' and 'commands' for existing items
        
    Returns:
        Complete HTML string
    """
    # Separate rules and commands
    global_rules = [r for r in global_recommendations if r.get("type", "").lower() == "rule"]
    global_commands = [r for r in global_recommendations if r.get("type", "").lower() == "command"]
    
    project_rules = {}
    project_commands = {}
    for project_path, recs in project_recommendations.items():
        project_rules[project_path] = [r for r in recs if r.get("type", "").lower() == "rule"]
        project_commands[project_path] = [r for r in recs if r.get("type", "").lower() == "command"]
    
    # Build Rules tab content
    rules_parts = []
    if global_rules:
        rules_parts.append('<div class="section">')
        rules_parts.append('<h2 class="section-title">Global Rules</h2>')
        rules_parts.append('<p style="color: rgba(237, 236, 236, 0.6); margin-bottom: 1.5rem;">These patterns appear across multiple projects and should be global rules.</p>')
        for i, rec in enumerate(global_rules):
            rules_parts.append(format_recommendation_html(rec, f"global-rule-{i}"))
        rules_parts.append('</div>')
    
    if project_rules:
        rules_parts.append('<div class="section">')
        rules_parts.append('<h2 class="section-title">Project-Specific Rules</h2>')
        for project_path, recs in project_rules.items():
            if recs:
                rules_parts.append('<div class="project-section">')
                rules_parts.append(f'<div class="project-header">{escape_html(project_path)}</div>')
                for i, rec in enumerate(recs):
                    rules_parts.append(format_recommendation_html(rec, f"project-{project_path}-rule-{i}"))
                rules_parts.append('</div>')
        rules_parts.append('</div>')
    
    if not global_rules and not project_rules:
        rules_parts.append('''
            <div class="empty-state">
                <div class="empty-state-icon">📋</div>
                <p>No rule recommendations found.</p>
            </div>
        ''')
    
    rules_content = '\n'.join(rules_parts)
    
    # Build Commands tab content
    commands_parts = []
    if global_commands:
        commands_parts.append('<div class="section">')
        commands_parts.append('<h2 class="section-title">Global Commands</h2>')
        commands_parts.append('<p style="color: rgba(237, 236, 236, 0.6); margin-bottom: 1.5rem;">These patterns appear across multiple projects and should be global commands.</p>')
        for i, rec in enumerate(global_commands):
            commands_parts.append(format_recommendation_html(rec, f"global-cmd-{i}"))
        commands_parts.append('</div>')
    
    if project_commands:
        commands_parts.append('<div class="section">')
        commands_parts.append('<h2 class="section-title">Project-Specific Commands</h2>')
        for project_path, recs in project_commands.items():
            if recs:
                commands_parts.append('<div class="project-section">')
                commands_parts.append(f'<div class="project-header">{escape_html(project_path)}</div>')
                for i, rec in enumerate(recs):
                    commands_parts.append(format_recommendation_html(rec, f"project-{project_path}-cmd-{i}"))
                commands_parts.append('</div>')
        commands_parts.append('</div>')
    
    if not global_commands and not project_commands:
        commands_parts.append('''
            <div class="empty-state">
                <div class="empty-state-icon">⚡</div>
                <p>No command recommendations found.</p>
            </div>
        ''')
    
    commands_content = '\n'.join(commands_parts)
    
    # Build Prompt Log tab content
    prompt_log_content = format_prompt_log_html(prompts or [])
    
    # Build Existing tab content
    existing_content = format_existing_html(existing or {'rules': [], 'commands': []})
    
    return HTML_TEMPLATE.format(
        rules_content=rules_content,
        commands_content=commands_content,
        prompt_log_content=prompt_log_content,
        existing_content=existing_content,
    )


def save_and_open_html(html_content: str) -> Path:
    """Save HTML content to a temporary file and open it in the browser.
    
    Args:
        html_content: HTML content to save
        
    Returns:
        Path to the saved HTML file
    """
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.html',
        delete=False,
        prefix='cursor-recommendations-'
    )
    
    temp_file.write(html_content)
    temp_file.close()
    
    file_path = Path(temp_file.name)
    
    # Open in browser
    webbrowser.open(f"file://{file_path.absolute()}")
    
    return file_path
