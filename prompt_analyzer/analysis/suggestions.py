"""Improvement suggestions generator."""

from typing import Dict, Any, List


def generate_suggestions(
    prompt: Dict[str, Any],
    quality_flags: List[str],
    detection_results: Dict[str, Any],
) -> List[str]:
    """Generate improvement suggestions based on quality flags.
    
    Args:
        prompt: Prompt dict
        quality_flags: List of quality flags
        detection_results: Detection results from detect_bad_prompts
    
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    if 'rejected_response' in quality_flags:
        suggestions.append(
            "Your prompt was rejected. Consider: "
            "1) Being more specific about what you want, "
            "2) Providing more context or examples, "
            "3) Breaking down complex requests into smaller steps."
        )
    
    if 'repeated_prompt' in quality_flags:
        repeated_info = detection_results.get('repeated', {})
        repeated_count = len(repeated_info.get('repeated_with', []))
        suggestions.append(
            f"You've sent {repeated_count + 1} similar prompts. "
            "Try consolidating your request or refining your prompt based on previous responses."
        )
    
    if 'vague_request' in quality_flags:
        suggestions.append(
            "Your prompt is vague. Try to: "
            "1) Be specific about what you want to accomplish, "
            "2) Include relevant context and constraints, "
            "3) Specify the desired output format if applicable."
        )
    
    # If no flags but prompt could be improved
    if not quality_flags:
        prompt_text = prompt.get('prompt_text', '')
        if len(prompt_text) < 50:
            suggestions.append(
                "Consider adding more context or details to help the AI understand your request better."
            )
    
    return suggestions

