"""HTML output generator for recommendations."""

import html
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import webbrowser


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
        
        .copy-button {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background-color: #26241e;
            color: #edecec;
            border: 1px solid #2b2923;
            border-radius: 4px;
            padding: 0.4rem 0.8rem;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background-color 0.2s;
        }}
        
        .copy-button:hover {{
            background-color: #2b2923;
        }}
        
        .copy-button:active {{
            background-color: #1b1913;
        }}
        
        .copy-button.copied {{
            background-color: #f54e00;
            color: #14120b;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Cursor Rules & Commands Recommendations</h1>
        <p class="subtitle">Generated from your recent prompts</p>
        
        {content}
    </div>
    
    <script>
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
        
        document.querySelectorAll('.copy-button').forEach(function(button) {{
            button.addEventListener('click', function() {{
                const contentBlock = this.parentElement.querySelector('.content-code');
                copyToClipboard(contentBlock.textContent, this);
            }});
        }});
    </script>
</body>
</html>"""


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return html.escape(text)


def format_recommendation_html(rec: Dict[str, Any], index: int) -> str:
    """Format a single recommendation as HTML.
    
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
                <button class="copy-button" id="copy-btn-{index}">Copy</button>
                <pre class="content-code">{content}</pre>
            </div>
            <div class="instructions">
                <div class="instructions-title">Where to place:</div>
                <div class="instructions-text">{instructions}</div>
            </div>
        </div>
    """
    
    return html_str


def generate_html(
    global_recommendations: List[Dict[str, Any]],
    project_recommendations: Dict[str, List[Dict[str, Any]]],
) -> str:
    """Generate HTML page from recommendations.
    
    Args:
        global_recommendations: List of global recommendations
        project_recommendations: Dictionary mapping project_path to recommendations
        
    Returns:
        Complete HTML string
    """
    content_parts = []
    
    # Global recommendations section
    if global_recommendations:
        content_parts.append('<div class="section">')
        content_parts.append('<h2 class="section-title">Global Recommendations</h2>')
        content_parts.append('<p style="color: rgba(237, 236, 236, 0.6); margin-bottom: 1.5rem;">These patterns appear across multiple projects and should be global rules or commands.</p>')
        
        for i, rec in enumerate(global_recommendations):
            content_parts.append(format_recommendation_html(rec, f"global-{i}"))
        
        content_parts.append('</div>')
    
    # Project-specific recommendations
    if project_recommendations:
        content_parts.append('<div class="section">')
        content_parts.append('<h2 class="section-title">Project-Specific Recommendations</h2>')
        
        for project_path, recs in project_recommendations.items():
            if recs:
                content_parts.append('<div class="project-section">')
                content_parts.append(f'<div class="project-header">{escape_html(project_path)}</div>')
                
                for i, rec in enumerate(recs):
                    content_parts.append(format_recommendation_html(rec, f"project-{project_path}-{i}"))
                
                content_parts.append('</div>')
        
        content_parts.append('</div>')
    
    # Empty state
    if not global_recommendations and not project_recommendations:
        content_parts.append('''
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No recommendations found. Try analyzing more prompts or a longer time range.</p>
            </div>
        ''')
    
    content = "\n".join(content_parts)
    return HTML_TEMPLATE.format(content=content)


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

