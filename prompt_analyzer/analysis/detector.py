"""Bad prompt detector."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .similarity import find_similar_prompts, SIMILARITY_THRESHOLD


def detect_repeated_prompt(
    prompt_id: str,
    prompt_text: str,
    timestamp: str,
    session_id: str,
    all_prompts: List[Dict[str, Any]],
    time_window_minutes: int = 5,
) -> Optional[Dict[str, Any]]:
    """Detect if a prompt is repeated within the same session or time window.
    
    Args:
        prompt_id: Current prompt ID
        prompt_text: Current prompt text
        timestamp: Current prompt timestamp (ISO8601)
        session_id: Current session ID
        all_prompts: List of all prompts from storage (dicts with id, prompt_text, timestamp, session_id)
        time_window_minutes: Time window for detection (default: 5 minutes)
    
    Returns:
        Dict with 'is_repeated' and 'repeated_with' list of prompt IDs, or None if not repeated
    """
    try:
        # Parse timestamp - handle various ISO formats
        timestamp_clean = timestamp.replace('Z', '+00:00')
        if '+' not in timestamp_clean and timestamp_clean.count(':') == 2:
            # No timezone, assume UTC
            timestamp_clean = timestamp_clean + '+00:00'
        
        current_time = datetime.fromisoformat(timestamp_clean)
        if current_time.tzinfo:
            current_time = current_time.replace(tzinfo=None)
    except (ValueError, AttributeError):
        # If parsing fails, skip time-based detection
        current_time = None
    
    time_threshold = None
    if current_time:
        time_threshold = current_time - timedelta(minutes=time_window_minutes)
    
    # Filter candidates: same session or within time window
    candidates = []
    for prompt in all_prompts:
        if prompt['id'] == prompt_id:
            continue
        
        # Check if in same session
        if prompt.get('session_id') == session_id:
            candidates.append((prompt['id'], prompt.get('prompt_text', '')))
        elif time_threshold:
            # Check if within time window
            try:
                prompt_timestamp = prompt.get('timestamp', '')
                if not prompt_timestamp:
                    continue
                    
                prompt_timestamp_clean = prompt_timestamp.replace('Z', '+00:00')
                if '+' not in prompt_timestamp_clean and prompt_timestamp_clean.count(':') == 2:
                    prompt_timestamp_clean = prompt_timestamp_clean + '+00:00'
                
                prompt_time = datetime.fromisoformat(prompt_timestamp_clean)
                if prompt_time.tzinfo:
                    prompt_time = prompt_time.replace(tzinfo=None)
                
                if prompt_time >= time_threshold:
                    candidates.append((prompt['id'], prompt.get('prompt_text', '')))
            except (ValueError, AttributeError, KeyError):
                continue
    
    if not candidates:
        return None
    
    # Find similar prompts
    similar = find_similar_prompts(prompt_text, candidates, threshold=SIMILARITY_THRESHOLD)
    
    if similar:
        return {
            'is_repeated': True,
            'repeated_with': [prompt_id for prompt_id, _ in similar],
        }
    
    return None


def detect_rejected_prompt(prompt: Dict[str, Any]) -> bool:
    """Detect if a prompt was rejected.
    
    Args:
        prompt: Prompt dict with 'user_action' field
    
    Returns:
        True if prompt was rejected
    """
    return prompt.get('user_action') == 'rejected'


def detect_vague_prompt(prompt_text: str) -> bool:
    """Detect if a prompt is vague (heuristic-based).
    
    Args:
        prompt_text: The prompt text to analyze
    
    Returns:
        True if prompt appears vague
    """
    if not prompt_text:
        return True
    
    text_lower = prompt_text.lower().strip()
    
    # Very short prompts (< 10 characters)
    if len(text_lower) < 10:
        return True
    
    # Common vague patterns
    vague_patterns = [
        'fix it',
        'make it better',
        'improve this',
        'do something',
        'help',
        'what',
        'how',
        'why',
        '?',  # Just a question mark
    ]
    
    # Check if prompt is just a vague pattern
    for pattern in vague_patterns:
        if text_lower == pattern or text_lower == pattern + '?':
            return True
    
    # Check if prompt is just a single word/question
    words = text_lower.split()
    if len(words) <= 2 and any(word.endswith('?') for word in words):
        return True
    
    return False


def detect_bad_prompts(
    prompt: Dict[str, Any],
    all_prompts: List[Dict[str, Any]],
    time_window_minutes: int = 5,
) -> Dict[str, Any]:
    """Detect all bad prompt indicators for a given prompt.
    
    Args:
        prompt: The prompt to analyze
        all_prompts: List of all prompts for comparison
        time_window_minutes: Time window for repeated prompt detection
    
    Returns:
        Dict with quality flags and detection results
    """
    flags = []
    detection_results = {}
    
    # Check for rejected prompt
    if detect_rejected_prompt(prompt):
        flags.append('rejected_response')
        detection_results['rejected'] = True
    
    # Check for repeated prompt
    repeated_info = detect_repeated_prompt(
        prompt['id'],
        prompt.get('prompt_text', ''),
        prompt.get('timestamp', ''),
        prompt.get('session_id', ''),
        all_prompts,
        time_window_minutes,
    )
    
    if repeated_info and repeated_info.get('is_repeated'):
        flags.append('repeated_prompt')
        detection_results['repeated'] = repeated_info
    
    # Check for vague prompt
    if detect_vague_prompt(prompt.get('prompt_text', '')):
        flags.append('vague_request')
        detection_results['vague'] = True
    
    return {
        'quality_flags': flags,
        'detection_results': detection_results,
    }

