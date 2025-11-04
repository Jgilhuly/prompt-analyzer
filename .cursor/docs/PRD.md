# Product Requirements Document: Prompt Analyzer

**Product Name:** Prompt Analyzer  
**Version:** v1.0 (Local MVP)  
**Date:** 2025-01-27

Prompt Analyzer is a local-first tool that captures user prompts sent to Cursor via Hooks, analyzes them for quality and effectiveness, and provides actionable suggestions for improvement.

## Goals

- Capture all prompts and responses sent to Cursor via Hooks
- Analyze prompt quality using established best practices
- Identify problematic prompts (rejected suggestions, repeated prompts)
- Provide actionable improvement suggestions
- Maintain complete data privacy through local-only storage

## User Flow

1. Install package: `pip install prompt-analyzer`
2. Run setup: `prompt-analyzer setup` (configures hooks and creates storage)
3. Use Cursor normally - prompts are captured automatically
4. Review periodically: `prompt-analyzer stats` and `prompt-analyzer examples`

## Core Features

### 1. Data Collection via Cursor Hooks

- Hooks write data directly to SQLite database (`~/.prompt-analyzer/data/prompts.db`)
- Captures: prompts, responses, user actions (accept/reject), timestamps, session metadata
- No server needed - direct file writes only
- SQLite WAL mode handles concurrent writes safely

### 2. Prompt Analysis (On-Demand)

Analysis runs when user executes `stats` or `examples` commands.

**Bad Prompt Criteria:**

1. **Rejected Suggestions** ⚠️
   - Prompts where `user_action` = "rejected"
   - Flags prompts for review and suggests improvements

2. **Repeated Sequential Prompts** 🔄
   - Same/similar prompts sent multiple times in sequence (>80% similarity)
   - Detects within same session or 5-minute window
   - Suggests consolidation

**Scoring:**
- Quality score (0-100) with deductions for bad prompts
- Quality flags: rejected_response, repeated_prompt, vague_request

### 3. CLI Commands

**`prompt-analyzer setup`**
- Creates `hooks.json` in `~/.cursor/`
- Generates hook scripts that write to SQLite
- Initializes storage directory and database
- Options: `--storage-path`, `--hooks-dir`, `--overwrite`

**`prompt-analyzer stats [--since 7d]`**
- Shows summary statistics (default: last 7 days)
- Displays: total prompts, quality trends, bad prompt highlights
- Runs analysis on-demand

**`prompt-analyzer examples [--type rejected|repeated|all] [--limit N]`**
- Shows example prompts with analysis and suggestions
- Filters by type and time range

**`prompt-analyzer storage`**
- Shows storage location, database size, prompt count

**`prompt-analyzer storage clear [--confirm] [--older-than 30d]`**
- Removes stored prompts (requires confirmation)

## Technical Architecture

### Package Distribution
- Installable Python package (`pip install prompt-analyzer`)
- Entry point: `prompt-analyzer` CLI command

### Technology Stack
- Python with SQLite (WAL mode)
- CLI Framework: Click or argparse
- NLP libraries for analysis (spaCy, NLTK, or lightweight alternatives)

### System Flow
```
Cursor IDE (Hooks) → Direct Write → SQLite → CLI Commands → Analysis Engine → Results
```

### File Structure
```
prompt-analyzer/
├── prompt_analyzer/
│   ├── cli/              # CLI commands
│   ├── hooks/           # Hook script generator & templates
│   ├── storage/         # SQLite operations
│   ├── analysis/        # Analysis engine (analyzer, scorer, suggestions, bad_prompt_detector)
│   └── ui/              # CLI dashboard & formatters
├── tests/
├── pyproject.toml
└── requirements.txt
```

**Storage Locations:**
- Database: `~/.prompt-analyzer/data/prompts.db`
- Config: `~/.prompt-analyzer/config.json`
- Hooks: `~/.cursor/hooks.json` and `~/.cursor/hooks/prompt-analyzer.js`

### Storage Schema
```json
{
  "id": "uuid",
  "timestamp": "ISO8601",
  "prompt_text": "string",
  "response_text": "string",
  "user_action": "accepted" | "rejected" | "edited" | null,
  "session_id": "uuid",
  "sequence_number": 1,
  "analysis": {
    "score": 0-100,
    "quality_flags": ["rejected_response", "repeated_prompt"],
    "suggestions": ["suggestion1", "suggestion2"],
    "is_repeated": false,
    "repeated_with": ["prompt_id_1"]
  }
}
```

## MVP Scope

### In Scope
- Installable Python package
- 5 CLI commands (setup, stats, examples, storage, storage clear)
- Hook integration with direct SQLite writes
- On-demand analysis
- Bad prompt detection (rejected, repeated)
- Basic scoring and suggestions

### Out of Scope
- Cloud storage/backup
- Web dashboard
- Real-time analysis
- Advanced ML models
- Multi-user support

## Success Criteria

- Captures 95%+ of prompts via hooks
- Correctly identifies 90%+ of rejected prompts
- Correctly identifies 85%+ of repeated prompts
- Setup takes < 5 minutes
- Analysis completes in < 5 seconds for < 1000 prompts
- Zero performance impact on Cursor

## References

- [Cursor Hooks Documentation](https://cursor.com/docs/agent/hooks#hooks)
