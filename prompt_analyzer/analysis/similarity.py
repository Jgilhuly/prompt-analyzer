"""Prompt similarity detection."""

from typing import List, Tuple

from thefuzz import fuzz


SIMILARITY_THRESHOLD = 80  # 80% similarity threshold per PRD


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using fuzzy string matching.
    
    Returns:
        Similarity score (0-100)
    """
    if not text1 or not text2:
        return 0.0
    
    # Use token_sort_ratio for better handling of reordered words
    return fuzz.token_sort_ratio(text1, text2)


def find_similar_prompts(
    prompt_text: str,
    candidate_prompts: List[Tuple[str, str]],  # List of (prompt_id, prompt_text)
    threshold: float = SIMILARITY_THRESHOLD,
) -> List[Tuple[str, float]]:
    """Find prompts similar to the given prompt.
    
    Args:
        prompt_text: The prompt to compare against
        candidate_prompts: List of (prompt_id, prompt_text) tuples
        threshold: Minimum similarity threshold (0-100)
    
    Returns:
        List of (prompt_id, similarity_score) tuples above threshold
    """
    similar = []
    
    for prompt_id, candidate_text in candidate_prompts:
        similarity = calculate_similarity(prompt_text, candidate_text)
        if similarity >= threshold:
            similar.append((prompt_id, similarity))
    
    # Sort by similarity (highest first)
    similar.sort(key=lambda x: x[1], reverse=True)
    return similar


def is_similar(text1: str, text2: str, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    """Check if two texts are similar above the threshold."""
    return calculate_similarity(text1, text2) >= threshold

