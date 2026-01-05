"""CLI commands for stats, examples, and storage."""

import click
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any

from ..storage import PromptStorage
from ..analysis import PromptAnalyzer
from ..storage.paths import get_database_path
from ..ui import format_stats, format_examples, format_storage_info, parse_time_range
from ..recommend.analyzer import analyze_project_prompts, analyze_cross_project_patterns
from ..recommend.html_output import generate_html, save_and_open_html
from ..recommend.scanner import scan_all_existing


def format_timestamp(iso_string: str) -> str:
    """Format ISO timestamp to readable string."""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_string


@click.command()
@click.option('--since', default='7d', help='Time range (e.g., 7d, 30d, 1h, 2w)')
def stats(since: str):
    """Show summary statistics and trends."""
    storage = PromptStorage()
    analyzer = PromptAnalyzer(storage)
    
    # Parse time range
    since_timestamp = parse_time_range(since)
    if since_timestamp is None:
        click.echo(f"Error: Invalid time range format '{since}'. Use format like '7d', '30d', '1h'", err=True)
        return
    
    # Get prompts in range
    prompts = storage.list(since=since_timestamp)
    
    if not prompts:
        click.echo(f"No prompts found in the last {since}.")
        return
    
    # Analyze prompts that haven't been analyzed
    click.echo("Analyzing prompts...", err=True)
    analysis_results = analyzer.analyze_prompts(since=since_timestamp)
    
    # Save analysis results back to storage
    for result in analysis_results:
        storage.update_analysis(result['prompt_id'], result['analysis'])
    
    # Refresh prompts with analysis
    prompts = storage.list(since=since_timestamp)
    
    # Calculate statistics
    total = len(prompts)
    
    # Quality breakdown
    quality_breakdown = {
        'rejected': 0,
        'repeated': 0,
        'accepted': 0,
        'edited': 0,
        'no_action': 0,
    }
    
    # Score statistics
    scores = []
    
    for prompt in prompts:
        # Count user actions
        action = prompt.get('user_action')
        if action == 'rejected':
            quality_breakdown['rejected'] += 1
        elif action == 'accepted':
            quality_breakdown['accepted'] += 1
        elif action == 'edited':
            quality_breakdown['edited'] += 1
        else:
            quality_breakdown['no_action'] += 1
        
        # Count repeated prompts
        if prompt.get('analysis', {}).get('is_repeated'):
            quality_breakdown['repeated'] += 1
        
        # Collect scores
        score = prompt.get('analysis', {}).get('score')
        if score is not None:
            scores.append(score)
    
    # Calculate score stats
    score_stats = {}
    if scores:
        score_stats = {
            'average': sum(scores) / len(scores),
            'median': sorted(scores)[len(scores) // 2],
            'min': min(scores),
            'max': max(scores),
        }
    
    # Calculate trends
    trends = []
    if len(prompts) > 1:
        # Split into two halves to compare
        mid = len(prompts) // 2
        first_half = prompts[mid:]
        second_half = prompts[:mid]
        
        first_rejected = sum(1 for p in first_half if p.get('user_action') == 'rejected')
        second_rejected = sum(1 for p in second_half if p.get('user_action') == 'rejected')
        
        if first_rejected > 0 and second_rejected > 0:
            rejection_rate_first = first_rejected / len(first_half) * 100
            rejection_rate_second = second_rejected / len(second_half) * 100
            
            if rejection_rate_second < rejection_rate_first:
                trends.append(f"✅ Rejection rate improved: {rejection_rate_first:.1f}% → {rejection_rate_second:.1f}%")
            elif rejection_rate_second > rejection_rate_first:
                trends.append(f"⚠️  Rejection rate increased: {rejection_rate_first:.1f}% → {rejection_rate_second:.1f}%")
    
    # Format date range
    if prompts:
        oldest = prompts[-1]['timestamp']
        newest = prompts[0]['timestamp']
        date_range = f"{format_timestamp(oldest)} to {format_timestamp(newest)}"
    else:
        date_range = "N/A"
    
    stats_dict = {
        'total_prompts': total,
        'date_range': date_range,
        'quality_breakdown': quality_breakdown,
        'score_stats': score_stats,
        'trends': trends,
    }
    
    click.echo(format_stats(stats_dict))


@click.command()
@click.option('--type', 'filter_type', type=click.Choice(['rejected', 'repeated', 'all'], case_sensitive=False), default='all', help='Filter by prompt type')
@click.option('--since', default='7d', help='Time range (e.g., 7d, 30d, 1h)')
@click.option('--limit', type=int, default=10, help='Maximum number of examples to show')
def examples(filter_type: str, since: str, limit: int):
    """Show example prompts with analysis and suggestions."""
    storage = PromptStorage()
    analyzer = PromptAnalyzer(storage)
    
    # Parse time range
    since_timestamp = parse_time_range(since)
    if since_timestamp is None:
        click.echo(f"Error: Invalid time range format '{since}'. Use format like '7d', '30d', '1h'", err=True)
        return
    
    # Get prompts
    prompts = storage.list(since=since_timestamp)
    
    if not prompts:
        click.echo(f"No prompts found in the last {since}.")
        return
    
    # Analyze prompts
    click.echo("Analyzing prompts...", err=True)
    analysis_results = analyzer.analyze_prompts(since=since_timestamp)
    
    # Save analysis results back to storage
    for result in analysis_results:
        storage.update_analysis(result['prompt_id'], result['analysis'])
    
    # Refresh prompts with analysis
    prompts = storage.list(since=since_timestamp)
    
    # Filter prompts
    filtered = []
    for prompt in prompts:
        if filter_type == 'rejected':
            if prompt.get('user_action') == 'rejected':
                filtered.append(prompt)
        elif filter_type == 'repeated':
            if prompt.get('analysis', {}).get('is_repeated'):
                filtered.append(prompt)
        else:  # all
            filtered.append(prompt)
    
    if not filtered:
        click.echo(f"No {filter_type} prompts found in the last {since}.")
        return
    
    # Display examples
    click.echo(format_examples(filtered, limit=limit))


@click.group(invoke_without_command=True)
@click.pass_context
def storage_group(ctx):
    """Storage management commands."""
    if ctx.invoked_subcommand is None:
        # Show info by default
        info()


@storage_group.command()
def info():
    """Show storage location and database information."""
    db_path = get_database_path()
    storage = PromptStorage()
    
    # Get database size
    db_size = "N/A"
    if db_path.exists():
        size_bytes = db_path.stat().st_size
        if size_bytes < 1024:
            db_size = f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            db_size = f"{size_bytes / 1024:.1f} KB"
        else:
            db_size = f"{size_bytes / (1024 * 1024):.1f} MB"
    
    # Get prompt count
    total_prompts = storage.count()
    
    # Get oldest and newest prompts
    all_prompts = storage.list(limit=1000)
    oldest_prompt = None
    newest_prompt = None
    
    if all_prompts:
        newest_prompt = all_prompts[0]['timestamp']
        oldest_prompt = all_prompts[-1]['timestamp']
    
    info_dict = {
        'database_path': str(db_path),
        'database_size': db_size,
        'total_prompts': total_prompts,
        'oldest_prompt': oldest_prompt,
        'newest_prompt': newest_prompt,
    }
    
    click.echo(format_storage_info(info_dict))


@storage_group.command()
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.option('--older-than', default=None, help='Only delete prompts older than this (e.g., 30d)')
def clear(confirm: bool, older_than: Optional[str]):
    """Clear stored prompts (requires confirmation)."""
    storage = PromptStorage()
    
    # Parse older_than if provided
    older_than_timestamp = None
    if older_than:
        older_than_timestamp = parse_time_range(older_than)
        if older_than_timestamp is None:
            click.echo(f"Error: Invalid time range format '{older_than}'. Use format like '30d', '1w'", err=True)
            return
    
    # Count what will be deleted
    if older_than_timestamp:
        count = storage.count()
        keep_count = storage.count(since=older_than_timestamp)
        delete_count = count - keep_count
        message = f"This will delete {delete_count} prompt(s) older than {older_than}. {keep_count} prompt(s) will be kept."
    else:
        delete_count = storage.count()
        message = f"This will delete ALL {delete_count} stored prompt(s). This action cannot be undone."
    
    if delete_count == 0:
        click.echo("No prompts to delete.")
        return
    
    # Confirmation
    if not confirm:
        click.echo(message)
        if not click.confirm('Are you sure you want to continue?'):
            click.echo("Cancelled.")
            return
    
    # Perform deletion
    try:
        if older_than_timestamp:
            deleted = storage.delete(older_than=older_than_timestamp, confirm=True)
        else:
            # Delete all - we need to delete individually or use a different approach
            # Since delete() requires either prompt_id or older_than, we'll use a very old timestamp
            very_old = (datetime.now(timezone.utc) - timedelta(days=36500)).isoformat().replace('+00:00', 'Z')
            deleted = storage.delete(older_than=very_old, confirm=True)
        
        click.echo(f"✅ Deleted {deleted} prompt(s).")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@click.command()
@click.option('--since', default='30d', help='Time range to analyze (e.g., 7d, 30d, 1h)')
@click.option('--project', default=None, help='Filter to specific project path')
@click.option('--no-open', is_flag=True, help='Print path instead of opening browser')
def recommend(since: str, project: Optional[str], no_open: bool):
    """Generate Cursor rules and commands recommendations from recent prompts."""
    storage = PromptStorage()
    
    # Parse time range
    since_timestamp = parse_time_range(since)
    if since_timestamp is None:
        click.echo(f"Error: Invalid time range format '{since}'. Use format like '7d', '30d', '1h'", err=True)
        return
    
    # Get all prompts for the log view
    all_prompts = storage.list(since=since_timestamp)
    
    # Determine project paths to scan and get prompts
    if project:
        project_paths_to_scan = [project] if project else []
        prompts = storage.list(since=since_timestamp, project_path=project)
        if not prompts:
            click.echo(f"No prompts found for project '{project}' in the last {since}.", err=True)
            return
        prompts_by_project = None
    else:
        # Get prompts grouped by project
        prompts_by_project = storage.list_by_project(since=since_timestamp)
        if not prompts_by_project:
            click.echo(f"No prompts found in the last {since}.", err=True)
            return
        project_paths_to_scan = [p for p in prompts_by_project.keys() if p]
        prompts = None
    
    # Scan for existing rules and commands early (before analysis)
    click.echo("Scanning for existing rules and commands...", err=True)
    existing = scan_all_existing(project_paths=project_paths_to_scan, include_cwd=True)
    
    # Analyze prompts
    if project:
        click.echo(f"Analyzing {len(prompts)} prompt(s) from project '{project}'...", err=True)
        
        # Analyze project-specific patterns
        project_recs = analyze_project_prompts(prompts, project_path=project, existing=existing)
        global_recs = []
        project_recommendations = {project: project_recs} if project_recs else {}
    else:
        
        total_prompts = sum(len(prompts) for prompts in prompts_by_project.values())
        click.echo(f"Analyzing {total_prompts} prompt(s) across {len(prompts_by_project)} project(s)...", err=True)
        
        # Analyze cross-project patterns
        click.echo("Looking for global patterns...", err=True)
        global_recs = analyze_cross_project_patterns(prompts_by_project, existing=existing)
        
        # Analyze each project
        project_recommendations = {}
        for project_path, prompts in prompts_by_project.items():
            click.echo(f"Analyzing project: {project_path}...", err=True)
            recs = analyze_project_prompts(prompts, project_path=project_path, existing=existing)
            if recs:
                project_recommendations[project_path] = recs
    
    # Generate HTML
    click.echo("Generating recommendations page...", err=True)
    html_content = generate_html(
        global_recs,
        project_recommendations,
        prompts=all_prompts,
        existing=existing,
    )
    
    # Save and open
    file_path = save_and_open_html(html_content)
    
    if no_open:
        click.echo(f"\nRecommendations saved to: {file_path}")
    else:
        click.echo(f"\n✅ Recommendations page opened in browser")
        click.echo(f"   File saved to: {file_path}")
    
    # Summary
    total_recs = len(global_recs) + sum(len(recs) for recs in project_recommendations.values())
    if total_recs > 0:
        click.echo(f"\nFound {total_recs} recommendation(s):")
        if global_recs:
            click.echo(f"  - {len(global_recs)} global")
        for project_path, recs in project_recommendations.items():
            if recs:
                click.echo(f"  - {len(recs)} for {project_path}")
    
    # Show existing count
    existing_count = len(existing.get('rules', [])) + len(existing.get('commands', []))
    if existing_count > 0:
        click.echo(f"\nFound {existing_count} existing rule(s)/command(s) ({len(existing.get('rules', []))} rules, {len(existing.get('commands', []))} commands)")

