"""CRUD operations for prompts."""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4

import sqlite3

from .database import Database
from .filters import should_exclude_prompt


class PromptStorage:
    """Storage operations for prompts."""

    def __init__(self, db: Optional[Database] = None):
        """Initialize prompt storage."""
        self.db = db or Database()

    def create(
        self,
        prompt_text: str,
        response_text: Optional[str] = None,
        user_action: Optional[str] = None,
        session_id: Optional[str] = None,
        sequence_number: Optional[int] = None,
        project_path: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new prompt record."""
        prompt_id = str(uuid4())
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

        if session_id is None:
            session_id = str(uuid4())

        if sequence_number is None:
            # Get the next sequence number for this session
            sequence_number = self._get_next_sequence_number(session_id)

        # Extract analysis data
        analysis_score = None
        analysis_flags = None
        analysis_suggestions = None
        analysis_is_repeated = 0
        analysis_repeated_with = None

        if analysis:
            analysis_score = analysis.get("score")
            flags = analysis.get("quality_flags", [])
            analysis_flags = json.dumps(flags) if flags else None
            suggestions = analysis.get("suggestions", [])
            analysis_suggestions = json.dumps(suggestions) if suggestions else None
            analysis_is_repeated = 1 if analysis.get("is_repeated", False) else 0
            repeated_with = analysis.get("repeated_with", [])
            analysis_repeated_with = json.dumps(repeated_with) if repeated_with else None

        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO prompts (
                id, timestamp, prompt_text, response_text, user_action,
                session_id, sequence_number, project_path,
                analysis_score, analysis_flags, analysis_suggestions,
                analysis_is_repeated, analysis_repeated_with
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prompt_id,
            timestamp,
            prompt_text,
            response_text,
            user_action,
            session_id,
            sequence_number,
            project_path,
            analysis_score,
            analysis_flags,
            analysis_suggestions,
            analysis_is_repeated,
            analysis_repeated_with,
        ))

        conn.commit()
        return prompt_id

    def get(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Get a prompt by ID."""
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_dict(row)

    def update_analysis(self, prompt_id: str, analysis: Dict[str, Any]):
        """Update analysis data for a prompt."""
        conn = self.db.connect()
        cursor = conn.cursor()

        analysis_score = analysis.get("score")
        flags = analysis.get("quality_flags", [])
        analysis_flags = json.dumps(flags) if flags else None
        suggestions = analysis.get("suggestions", [])
        analysis_suggestions = json.dumps(suggestions) if suggestions else None
        analysis_is_repeated = 1 if analysis.get("is_repeated", False) else 0
        repeated_with = analysis.get("repeated_with", [])
        analysis_repeated_with = json.dumps(repeated_with) if repeated_with else None

        cursor.execute("""
            UPDATE prompts SET
                analysis_score = ?,
                analysis_flags = ?,
                analysis_suggestions = ?,
                analysis_is_repeated = ?,
                analysis_repeated_with = ?
            WHERE id = ?
        """, (
            analysis_score,
            analysis_flags,
            analysis_suggestions,
            analysis_is_repeated,
            analysis_repeated_with,
            prompt_id,
        ))

        conn.commit()

    def list(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        since: Optional[str] = None,
        user_action: Optional[str] = None,
        session_id: Optional[str] = None,
        project_path: Optional[str] = None,
        include_excluded: bool = False,
    ) -> List[Dict[str, Any]]:
        """List prompts with optional filters.
        
        Args:
            limit: Maximum number of prompts to return
            offset: Number of prompts to skip
            since: ISO timestamp to filter prompts
            user_action: Filter by user action
            session_id: Filter by session ID
            include_excluded: If True, include prompts that would normally be excluded
            
        Returns:
            List of prompt dictionaries
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM prompts WHERE 1=1"
        params = []

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        if user_action:
            query += " AND user_action = ?"
            params.append(user_action)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        if offset:
            query += " OFFSET ?"
            params.append(offset)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        prompts = [self._row_to_dict(row) for row in rows]
        
        # Filter out excluded prompts unless explicitly requested
        if not include_excluded:
            prompts = [
                prompt for prompt in prompts
                if not should_exclude_prompt(prompt.get('prompt_text', ''))
            ]
        
        return prompts

    def count(
        self,
        since: Optional[str] = None,
        user_action: Optional[str] = None,
        session_id: Optional[str] = None,
        project_path: Optional[str] = None,
        include_excluded: bool = False,
    ) -> int:
        """Count prompts with optional filters.
        
        Args:
            since: ISO timestamp to filter prompts
            user_action: Filter by user action
            session_id: Filter by session ID
            include_excluded: If True, include prompts that would normally be excluded
            
        Returns:
            Number of prompts matching the filters
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM prompts WHERE 1=1"
        params = []

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        if user_action:
            query += " AND user_action = ?"
            params.append(user_action)

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        prompts = [self._row_to_dict(row) for row in rows]
        
        # Filter out excluded prompts unless explicitly requested
        if not include_excluded:
            prompts = [
                prompt for prompt in prompts
                if not should_exclude_prompt(prompt.get('prompt_text', ''))
            ]
        
        return len(prompts)

    def delete(
        self,
        prompt_id: Optional[str] = None,
        older_than: Optional[str] = None,
        confirm: bool = False,
    ) -> int:
        """Delete prompts. Requires confirmation unless prompt_id is specified."""
        if not confirm and prompt_id is None:
            raise ValueError("Bulk delete requires confirmation")

        conn = self.db.connect()
        cursor = conn.cursor()

        if prompt_id:
            cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        elif older_than:
            cursor.execute("DELETE FROM prompts WHERE timestamp < ?", (older_than,))
        else:
            raise ValueError("Must specify either prompt_id or older_than")

        conn.commit()
        return cursor.rowcount

    def _get_next_sequence_number(self, session_id: str) -> int:
        """Get the next sequence number for a session."""
        conn = self.db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(sequence_number) FROM prompts WHERE session_id = ?
        """, (session_id,))

        result = cursor.fetchone()[0]
        return (result or 0) + 1

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        result = {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "prompt_text": row["prompt_text"],
            "response_text": row["response_text"],
            "user_action": row["user_action"],
            "session_id": row["session_id"],
            "sequence_number": row["sequence_number"],
        }

        # Parse analysis fields
        analysis = {}
        if row["analysis_score"] is not None:
            analysis["score"] = row["analysis_score"]
        if row["analysis_flags"]:
            analysis["quality_flags"] = json.loads(row["analysis_flags"])
        if row["analysis_suggestions"]:
            analysis["suggestions"] = json.loads(row["analysis_suggestions"])
        if row["analysis_is_repeated"]:
            analysis["is_repeated"] = True
        if row["analysis_repeated_with"]:
            analysis["repeated_with"] = json.loads(row["analysis_repeated_with"])

        if analysis:
            result["analysis"] = analysis

        # Add project_path if present
        if "project_path" in row.keys() and row["project_path"]:
            result["project_path"] = row["project_path"]

        return result
    
    def list_by_project(
        self,
        since: Optional[str] = None,
        limit: Optional[int] = None,
        include_excluded: bool = False,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List prompts grouped by project path.
        
        Args:
            since: ISO timestamp to filter prompts
            limit: Maximum number of prompts per project
            include_excluded: If True, include prompts that would normally be excluded
            
        Returns:
            Dictionary mapping project_path to list of prompts
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM prompts WHERE 1=1"
        params = []

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        prompts = [self._row_to_dict(row) for row in rows]
        
        # Filter out excluded prompts unless explicitly requested
        if not include_excluded:
            prompts = [
                prompt for prompt in prompts
                if not should_exclude_prompt(prompt.get('prompt_text', ''))
            ]
        
        # Group by project_path
        by_project: Dict[str, List[Dict[str, Any]]] = {}
        for prompt in prompts:
            project_path = prompt.get('project_path') or 'unknown'
            if project_path not in by_project:
                by_project[project_path] = []
            by_project[project_path].append(prompt)
        
        # Apply limit per project if specified
        if limit:
            for project_path in by_project:
                by_project[project_path] = by_project[project_path][:limit]
        
        return by_project
    
    def get_unique_projects(
        self,
        since: Optional[str] = None,
    ) -> List[str]:
        """Get list of unique project paths.
        
        Args:
            since: ISO timestamp to filter prompts
            
        Returns:
            List of unique project paths
        """
        conn = self.db.connect()
        cursor = conn.cursor()

        query = "SELECT DISTINCT project_path FROM prompts WHERE project_path IS NOT NULL"
        params = []

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [row[0] for row in rows if row[0]]

