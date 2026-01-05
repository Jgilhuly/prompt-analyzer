#!/usr/bin/env python3
"""Temporary script to scan for existing Cursor rules and commands."""

import sys
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from prompt_analyzer.recommend.scanner import scan_all_existing
import json

if __name__ == "__main__":
    result = scan_all_existing(include_cwd=True)
    
    print("=" * 80)
    print("CURSOR RULES AND COMMANDS IN THIS WORKSPACE")
    print("=" * 80)
    print()
    
    rules = result.get('rules', [])
    commands = result.get('commands', [])
    
    if not rules and not commands:
        print("No Cursor rules or commands found in this workspace.")
        print()
        print("Checked locations:")
        print("  - Project: .cursor/rules/ and .cursor/commands/")
        print("  - User global: ~/.cursor/rules/ and ~/.cursor/commands/")
    else:
        if rules:
            print(f"RULES ({len(rules)} found):")
            print("-" * 80)
            for rule in rules:
                print(f"\nName: {rule['name']}")
                print(f"Scope: {rule['scope']}")
                print(f"Source: {rule['source_path']}")
                print(f"Content preview:")
                content_preview = rule['content'][:200] + "..." if len(rule['content']) > 200 else rule['content']
                print(f"  {content_preview}")
                print()
        
        if commands:
            print(f"\nCOMMANDS ({len(commands)} found):")
            print("-" * 80)
            for cmd in commands:
                print(f"\nName: {cmd['name']}")
                print(f"Scope: {cmd['scope']}")
                print(f"Source: {cmd['source_path']}")
                print(f"Content preview:")
                content_preview = cmd['content'][:200] + "..." if len(cmd['content']) > 200 else cmd['content']
                print(f"  {content_preview}")
                print()
