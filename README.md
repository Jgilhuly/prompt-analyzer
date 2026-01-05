# Cursor Prompts

A local-first tool that captures and analyzes Cursor prompts for quality and effectiveness.

## Installation

```bash
pip install cursor-prompts
```

## Setup

1. **Configure hooks**:
   ```bash
   cursor-prompts setup
   ```
   This creates hooks in `~/.cursor/` and initializes storage in `~/.prompt-analyzer/`.

2. **Use Cursor normally** - prompts are captured automatically.

3. **Review your prompts**:
   ```bash
   cursor-prompts stats              # View statistics
   cursor-prompts examples --type rejected  # See problematic prompts
   cursor-prompts recommend          # Generate Cursor rules and commands recommendations
   ```

## Quick Commands

- `cursor-prompts stats [--since 7d]` - Show summary statistics
- `cursor-prompts examples [--type rejected|repeated|all] [--limit N]` - Show examples
- `cursor-prompts recommend [--since 30d] [--project PATH] [--no-open]` - Generate Cursor rules and commands recommendations from recent prompts
- `cursor-prompts storage` - Show storage info
- `cursor-prompts storage clear [--older-than 30d]` - Clear old prompts

## Analysis Criteria

Prompts are scored 0-100 with deductions for:

- **Rejected Suggestions** (-30): AI response was rejected
- **Repeated Prompts** (-20): Same/similar prompt sent multiple times (>80% similarity within session or 5-minute window)
- **Vague Requests** (-15): Very short prompts or single-word questions lacking context

The tool provides contextual suggestions for improvement based on detected issues.

## Recommendations

The `recommend` command analyzes your prompts to generate Cursor rules and commands recommendations:

- **Global patterns**: Identifies common patterns across all your projects
- **Project-specific**: Generates recommendations tailored to specific projects
- **Existing detection**: Scans for existing `.cursorrules` files and commands to avoid duplicates
- **Interactive HTML**: Opens a browser page with all recommendations, organized by project

Example usage:
```bash
cursor-prompts recommend                    # Analyze last 30 days
cursor-prompts recommend --since 7d        # Analyze last 7 days
cursor-prompts recommend --project /path   # Analyze specific project
cursor-prompts recommend --no-open         # Save HTML without opening browser
```

## Storage

All data is stored locally:
- Database: `~/.prompt-analyzer/data/prompts.db`
- Config: `~/.prompt-analyzer/config.json`
- Hooks: `~/.cursor/hooks.json` and `~/.cursor/hooks/cursor-prompts.js`

## Requirements

- Python 3.8+
- Cursor IDE
- Node.js (for hook execution)

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License
