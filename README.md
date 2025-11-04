# Prompt Analyzer

A local-first tool that captures and analyzes Cursor prompts for quality and effectiveness.

## Installation

```bash
pip install prompt-analyzer
```

## Setup

1. **Configure hooks**:
   ```bash
   prompt-analyzer setup
   ```
   This creates hooks in `~/.cursor/` and initializes storage in `~/.prompt-analyzer/`.

2. **Use Cursor normally** - prompts are captured automatically.

3. **Review your prompts**:
   ```bash
   prompt-analyzer stats              # View statistics
   prompt-analyzer examples --type rejected  # See problematic prompts
   ```

## Quick Commands

- `prompt-analyzer stats [--since 7d]` - Show summary statistics
- `prompt-analyzer examples [--type rejected|repeated|all] [--limit N]` - Show examples
- `prompt-analyzer storage` - Show storage info
- `prompt-analyzer storage clear [--older-than 30d]` - Clear old prompts

## Analysis Criteria

Prompts are scored 0-100 with deductions for:

- **Rejected Suggestions** (-30): AI response was rejected
- **Repeated Prompts** (-20): Same/similar prompt sent multiple times (>80% similarity within session or 5-minute window)
- **Vague Requests** (-15): Very short prompts or single-word questions lacking context

The tool provides contextual suggestions for improvement based on detected issues.

## Storage

All data is stored locally:
- Database: `~/.prompt-analyzer/data/prompts.db`
- Config: `~/.prompt-analyzer/config.json`
- Hooks: `~/.cursor/hooks.json` and `~/.cursor/hooks/prompt-analyzer.js`

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
