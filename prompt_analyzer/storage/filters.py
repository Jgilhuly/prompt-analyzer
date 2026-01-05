"""Filter configuration for excluding prompts from analysis."""

EXCLUDED_PROMPTS = [
    "Issue reproduced, please proceed.",
    "The issue has been fixed. Please clean up the instrumentation.",
    """Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.""",
]


def should_exclude_prompt(prompt_text: str) -> bool:
    """Return True if prompt should be excluded from analysis.
    
    Args:
        prompt_text: The prompt text to check
        
    Returns:
        True if the prompt should be excluded, False otherwise
    """
    if not prompt_text or not prompt_text.strip():
        return True
    return prompt_text.strip() in EXCLUDED_PROMPTS

