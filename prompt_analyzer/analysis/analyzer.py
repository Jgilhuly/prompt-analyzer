"""Main analysis engine."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from ..storage import PromptStorage

from .detector import detect_bad_prompts
from .scorer import score_prompt
from .suggestions import generate_suggestions


class PromptAnalyzer:
    """Main analysis engine for prompts."""
    
    def __init__(self, storage: Optional[PromptStorage] = None):
        """Initialize analyzer."""
        self.storage = storage or PromptStorage()
    
    def analyze_prompt(
        self,
        prompt_id: str,
        time_window_minutes: int = 5,
    ) -> Dict[str, Any]:
        """Analyze a single prompt.
        
        Args:
            prompt_id: ID of the prompt to analyze
            time_window_minutes: Time window for repeated prompt detection
        
        Returns:
            Analysis dict with score, flags, suggestions, etc.
        """
        prompt = self.storage.get(prompt_id)
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")
        
        # Get recent prompts for comparison
        # Get prompts from the last hour for comparison
        cutoff_time = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat().replace('+00:00', 'Z')
        
        recent_prompts = self.storage.list(
            since=cutoff_time,
            limit=1000,  # Reasonable limit for analysis
        )
        
        # Detect bad prompts
        detection_results = detect_bad_prompts(
            prompt,
            recent_prompts,
            time_window_minutes,
        )
        
        quality_flags = detection_results.get('quality_flags', [])
        
        # Calculate score
        score = score_prompt(prompt, detection_results)
        
        # Generate suggestions
        suggestions = generate_suggestions(
            prompt,
            quality_flags,
            detection_results.get('detection_results', {}),
        )
        
        # Build analysis result
        analysis = {
            'score': score,
            'quality_flags': quality_flags,
            'suggestions': suggestions,
        }
        
        # Add repeated prompt info if detected
        repeated_info = detection_results.get('detection_results', {}).get('repeated')
        if repeated_info:
            analysis['is_repeated'] = repeated_info.get('is_repeated', False)
            analysis['repeated_with'] = repeated_info.get('repeated_with', [])
        else:
            analysis['is_repeated'] = False
            analysis['repeated_with'] = []
        
        return analysis
    
    def analyze_prompts(
        self,
        prompt_ids: Optional[List[str]] = None,
        since: Optional[str] = None,
        limit: Optional[int] = None,
        time_window_minutes: int = 5,
    ) -> List[Dict[str, Any]]:
        """Analyze multiple prompts.
        
        Args:
            prompt_ids: Optional list of specific prompt IDs to analyze
            since: Optional ISO timestamp to filter prompts
            limit: Optional limit on number of prompts to analyze
            time_window_minutes: Time window for repeated prompt detection
        
        Returns:
            List of analysis dicts with prompt_id and analysis
        """
        if prompt_ids:
            prompts_to_analyze = [
                self.storage.get(pid) for pid in prompt_ids
            ]
            prompts_to_analyze = [p for p in prompts_to_analyze if p]
        else:
            prompts_to_analyze = self.storage.list(since=since, limit=limit)
        
        # Get all prompts for comparison
        cutoff_time = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat().replace('+00:00', 'Z')
        
        all_prompts = self.storage.list(since=cutoff_time, limit=1000)
        
        results = []
        for prompt in prompts_to_analyze:
            try:
                detection_results = detect_bad_prompts(
                    prompt,
                    all_prompts,
                    time_window_minutes,
                )
                
                quality_flags = detection_results.get('quality_flags', [])
                score = score_prompt(prompt, detection_results)
                suggestions = generate_suggestions(
                    prompt,
                    quality_flags,
                    detection_results.get('detection_results', {}),
                )
                
                repeated_info = detection_results.get('detection_results', {}).get('repeated')
                
                analysis = {
                    'prompt_id': prompt['id'],
                    'analysis': {
                        'score': score,
                        'quality_flags': quality_flags,
                        'suggestions': suggestions,
                        'is_repeated': repeated_info.get('is_repeated', False) if repeated_info else False,
                        'repeated_with': repeated_info.get('repeated_with', []) if repeated_info else [],
                    },
                }
                
                results.append(analysis)
            except Exception as e:
                # Log error but continue with other prompts
                # In production, you might want to log this properly
                continue
        
        return results
    
    def update_prompt_analysis(self, prompt_id: str, time_window_minutes: int = 5):
        """Analyze a prompt and update its analysis in storage.
        
        Args:
            prompt_id: ID of the prompt to analyze
            time_window_minutes: Time window for repeated prompt detection
        """
        analysis = self.analyze_prompt(prompt_id, time_window_minutes)
        self.storage.update_analysis(prompt_id, analysis)

