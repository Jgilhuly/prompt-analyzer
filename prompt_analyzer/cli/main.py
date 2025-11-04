"""Main CLI entry point."""

import click

from .setup import setup
from .commands import stats, examples, storage_group


@click.group()
def cli():
    """Prompt Analyzer - Analyze your Cursor prompts for quality and effectiveness."""
    pass


# Register commands
cli.add_command(setup)
cli.add_command(stats)
cli.add_command(examples)
cli.add_command(storage_group, name='storage')


if __name__ == "__main__":
    cli()

