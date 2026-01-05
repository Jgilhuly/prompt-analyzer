"""Setup command for cursor-prompts."""

import click
from pathlib import Path

from ..hooks import install_hooks
from ..storage import Database, ensure_directories


@click.command()
@click.option(
    "--storage-path",
    type=click.Path(path_type=Path),
    help="Custom path for the SQLite database (default: ~/.prompt-analyzer/data/prompts.db)",
)
@click.option(
    "--hooks-dir",
    type=click.Path(path_type=Path),
    help="Custom directory for Cursor hooks (default: ~/.cursor)",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing hooks configuration",
)
def setup(storage_path: Path, hooks_dir: Path, overwrite: bool):
    """Initialize cursor-prompts: set up storage and install Cursor hooks."""
    click.echo("Setting up cursor-prompts...")
    
    # Initialize storage
    click.echo("Initializing storage...")
    try:
        ensure_directories()
        
        # Initialize database schema
        db = Database(storage_path)
        db.initialize_schema()
        db.close()
        
        db_path = storage_path or db.db_path
        click.echo(f"✓ Database initialized at {db_path}")
    except Exception as e:
        click.echo(f"✗ Failed to initialize storage: {e}", err=True)
        raise click.Abort()
    
    # Install hooks
    click.echo("Installing Cursor hooks...")
    click.echo("Checking Node.js dependencies...")
    success, message = install_hooks(
        storage_path=storage_path,
        hooks_dir=hooks_dir,
        overwrite=overwrite,
        check_dependencies=True,
    )
    
    if success:
        click.echo(f"✓ {message}")
        click.echo("\nSetup complete! Prompts will now be captured automatically.")
        click.echo("Use 'cursor-prompts stats' to view your prompt statistics.")
    else:
        click.echo(f"✗ {message}", err=True)
        raise click.Abort()

