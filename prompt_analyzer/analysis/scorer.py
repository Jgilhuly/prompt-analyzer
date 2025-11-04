"""Quality scoring algorithm."""

from typing import Dict, Any, List


BASE_SCORE = 100  # Start with perfect score
REJECTED_DEDUCTION = 30  # Points deducted for rejected response
REPEATED_DEDUCTION = 20  # Points deducted for repeated prompt
VAGUE_DEDUCTION = 15  # Points deducted for vague request


def calculate_score(prompt: Dict[str, Any], quality_flags: List[str]) -> int:
    """Calculate quality score for a prompt (0-100 scale).
    
    Args:
        prompt: Prompt dict
        quality_flags: List of quality flags
    
    Returns:
        Quality score (0-100)
    """
    score = BASE_SCORE
    
    # Apply deductions based on flags
    if 'rejected_response' in quality_flags:
        score -= REJECTED_DEDUCTION
    
    if 'repeated_prompt' in quality_flags:
        score -= REPEATED_DEDUCTION
    
    if 'vague_request' in quality_flags:
        score -= VAGUE_DEDUCTION
    
    # Ensure score is within bounds
    score = max(0, min(100, score))
    
    return score


def score_prompt(prompt: Dict[str, Any], detection_results: Dict[str, Any]) -> int:
    """Score a prompt based on detection results.
    
    Args:
        prompt: Prompt dict
        detection_results: Results from detect_bad_prompts
    
    Returns:
        Quality score (0-100)
    """
    quality_flags = detection_results.get('quality_flags', [])
    return calculate_score(prompt, quality_flags)

