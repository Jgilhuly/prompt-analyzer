"""UI formatters for CLI output."""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone


def format_timestamp(iso_string: str) -> str:
    """Format ISO timestamp to readable string."""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_string


def format_stats(stats: Dict[str, Any]) -> str:
    """Format statistics for display."""
    lines = []
    lines.append("📊 Prompt Statistics")
    lines.append("=" * 50)
    lines.append("")
    
    # Overview
    lines.append(f"Total Prompts: {stats.get('total_prompts', 0)}")
    lines.append(f"Date Range: {stats.get('date_range', 'N/A')}")
    lines.append("")
    
    # Quality breakdown
    if 'quality_breakdown' in stats:
        qb = stats['quality_breakdown']
        lines.append("Quality Breakdown:")
        lines.append(f"  ⚠️  Rejected: {qb.get('rejected', 0)}")
        lines.append(f"  🔄 Repeated: {qb.get('repeated', 0)}")
        lines.append(f"  ✅ Accepted: {qb.get('accepted', 0)}")
        lines.append(f"  ✏️  Edited: {qb.get('edited', 0)}")
        lines.append(f"  ⏸️  No Action: {qb.get('no_action', 0)}")
        lines.append("")
    
    # Score statistics
    if 'score_stats' in stats:
        ss = stats['score_stats']
        lines.append("Quality Scores:")
        lines.append(f"  Average: {ss.get('average', 0):.1f}")
        lines.append(f"  Median: {ss.get('median', 0):.1f}")
        lines.append(f"  Min: {ss.get('min', 0)}")
        lines.append(f"  Max: {ss.get('max', 0)}")
        lines.append("")
    
    # Trends
    if 'trends' in stats and stats['trends']:
        lines.append("Trends:")
        for trend in stats['trends']:
            lines.append(f"  {trend}")
        lines.append("")
    
    return "\n".join(lines)


def format_example(prompt: Dict[str, Any], include_analysis: bool = True) -> str:
    """Format a single prompt example."""
    lines = []
    
    # Header
    lines.append("─" * 70)
    lines.append(f"Prompt ID: {prompt['id']}")
    lines.append(f"Timestamp: {format_timestamp(prompt['timestamp'])}")
    
    if prompt.get('session_id'):
        lines.append(f"Session: {prompt['session_id'][:8]}...")
    
    if prompt.get('user_action'):
        action_emoji = {
            'accepted': '✅',
            'rejected': '⚠️',
            'edited': '✏️'
        }.get(prompt['user_action'], '⏸️')
        lines.append(f"Action: {action_emoji} {prompt['user_action']}")
    
    lines.append("")
    
    # Prompt text
    prompt_text = prompt.get('prompt_text', '')
    lines.append("Prompt:")
    # Truncate long prompts
    if len(prompt_text) > 500:
        lines.append(prompt_text[:500] + "...")
    else:
        lines.append(prompt_text)
    lines.append("")
    
    # Analysis
    if include_analysis and 'analysis' in prompt:
        analysis = prompt['analysis']
        
        # Score
        score = analysis.get('score')
        if score is not None:
            score_emoji = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            lines.append(f"Quality Score: {score_emoji} {score}/100")
        
        # Flags
        flags = analysis.get('quality_flags', [])
        if flags:
            flag_emojis = {
                'rejected_response': '⚠️',
                'repeated_prompt': '🔄',
                'vague_request': '❓'
            }
            flag_display = [f"{flag_emojis.get(f, '•')} {f}" for f in flags]
            lines.append(f"Flags: {', '.join(flag_display)}")
        
        # Suggestions
        suggestions = analysis.get('suggestions', [])
        if suggestions:
            lines.append("")
            lines.append("Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"  {i}. {suggestion}")
        
        # Repeated with
        if analysis.get('is_repeated') and analysis.get('repeated_with'):
            lines.append("")
            lines.append(f"🔄 Repeated with: {len(analysis['repeated_with'])} other prompt(s)")
    
    lines.append("")
    
    return "\n".join(lines)


def format_examples(examples: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
    """Format multiple prompt examples."""
    lines = []
    
    if not examples:
        lines.append("No prompts found matching the criteria.")
        return "\n".join(lines)
    
    lines.append(f"Found {len(examples)} prompt(s)")
    lines.append("")
    
    # Limit if specified
    display_examples = examples[:limit] if limit else examples
    
    for i, prompt in enumerate(display_examples, 1):
        lines.append(format_example(prompt, include_analysis=True))
        if i < len(display_examples):
            lines.append("")
    
    return "\n".join(lines)


def format_storage_info(info: Dict[str, Any]) -> str:
    """Format storage information."""
    lines = []
    lines.append("💾 Storage Information")
    lines.append("=" * 50)
    lines.append("")
    
    lines.append(f"Database Path: {info.get('database_path', 'N/A')}")
    lines.append(f"Database Size: {info.get('database_size', 'N/A')}")
    lines.append(f"Total Prompts: {info.get('total_prompts', 0)}")
    
    if 'oldest_prompt' in info:
        lines.append(f"Oldest Prompt: {format_timestamp(info['oldest_prompt'])}")
    
    if 'newest_prompt' in info:
        lines.append(f"Newest Prompt: {format_timestamp(info['newest_prompt'])}")
    
    lines.append("")
    
    return "\n".join(lines)


def parse_time_range(time_str: str) -> Optional[str]:
    """Parse time range string like '7d', '30d', '1h' to ISO timestamp.
    
    Returns ISO timestamp string for the cutoff time, or None if invalid.
    """
    if not time_str:
        return None
    
    try:
        # Parse format like "7d", "30d", "1h", "2w"
        time_str = time_str.lower().strip()
        
        if time_str.endswith('d'):
            days = int(time_str[:-1])
            delta = datetime.now(timezone.utc) - timedelta(days=days)
        elif time_str.endswith('h'):
            hours = int(time_str[:-1])
            delta = datetime.now(timezone.utc) - timedelta(hours=hours)
        elif time_str.endswith('w'):
            weeks = int(time_str[:-1])
            delta = datetime.now(timezone.utc) - timedelta(weeks=weeks)
        elif time_str.endswith('m'):
            # Try months (approximate as 30 days)
            months = int(time_str[:-1])
            delta = datetime.now(timezone.utc) - timedelta(days=months * 30)
        else:
            return None
        
        return delta.isoformat() + "Z"
    except (ValueError, AttributeError):
        return None

