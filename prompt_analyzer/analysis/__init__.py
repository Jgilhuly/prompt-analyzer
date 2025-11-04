"""Analysis engine module (analyzer, scorer, suggestions, bad_prompt_detector)."""

from .analyzer import PromptAnalyzer
from .similarity import calculate_similarity, find_similar_prompts, is_similar
from .detector import (
    detect_repeated_prompt,
    detect_rejected_prompt,
    detect_vague_prompt,
    detect_bad_prompts,
)
from .scorer import calculate_score, score_prompt
from .suggestions import generate_suggestions

__all__ = [
    "PromptAnalyzer",
    "calculate_similarity",
    "find_similar_prompts",
    "is_similar",
    "detect_repeated_prompt",
    "detect_rejected_prompt",
    "detect_vague_prompt",
    "detect_bad_prompts",
    "calculate_score",
    "score_prompt",
    "generate_suggestions",
]

