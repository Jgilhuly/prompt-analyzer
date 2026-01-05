"""Cursor CLI integration for pattern analysis and recommendation generation."""

import json
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path


def format_prompts_for_analysis(prompts: List[Dict[str, Any]], max_prompts: int = 50) -> str:
    """Format prompts for analysis by cursor-agent.
    
    Args:
        prompts: List of prompt dictionaries
        max_prompts: Maximum number of prompts to include
        
    Returns:
        Formatted string for analysis
    """
    # Truncate if too many prompts
    prompts_to_analyze = prompts[:max_prompts]
    
    formatted = []
    for i, prompt in enumerate(prompts_to_analyze, 1):
        prompt_text = prompt.get('prompt_text', '')[:500]  # Truncate long prompts
        timestamp = prompt.get('timestamp', '')
        user_action = prompt.get('user_action', '')
        
        entry = f"Prompt {i} ({timestamp})"
        if user_action:
            entry += f" [Action: {user_action}]"
        entry += f":\n{prompt_text}\n"
        
        formatted.append(entry)
    
    if len(prompts) > max_prompts:
        formatted.append(f"\n... and {len(prompts) - max_prompts} more prompts")
    
    return "\n".join(formatted)


def generate_recommendations_prompt(
    prompts: List[Dict[str, Any]],
    scope: str = "project",
    project_path: Optional[str] = None,
) -> str:
    """Generate the prompt to send to cursor-agent for analysis.
    
    Args:
        prompts: List of prompt dictionaries to analyze
        scope: Either "project" or "global"
        project_path: Optional project path for context
        
    Returns:
        Formatted prompt string
    """
    formatted_prompts = format_prompts_for_analysis(prompts)
    
    scope_context = ""
    if scope == "project" and project_path:
        scope_context = f"\n\nThese prompts are from the project: {project_path}"
    elif scope == "global":
        scope_context = "\n\nThese prompts span multiple projects. Look for patterns that would benefit from global rules or commands."
    
    prompt = f"""Analyze these prompts from a coding session and identify patterns that would benefit from Cursor rules or commands.{scope_context}

{formatted_prompts}

For each pattern you identify, provide:
1. Type: Either "Rule" (for persistent guidance/instructions) or "Command" (for actions to invoke)
2. Name: A descriptive name for the rule/command
3. Content: The complete rule or command content in proper format
4. Reasoning: Why this pattern warrants automation

Format your response as JSON with this structure:
{{
  "recommendations": [
    {{
      "type": "Rule" or "Command",
      "name": "descriptive name",
      "content": "full rule/command content",
      "reasoning": "explanation"
    }}
  ]
}}

Focus on patterns that:
- Are repeated frequently
- Represent coding style preferences
- Define workflows that could be automated
- Capture domain-specific conventions
- Would benefit from being persistent or reusable

Return only valid JSON, no additional text before or after."""
    
    return prompt


def call_cursor_agent(prompt: str) -> Optional[Dict[str, Any]]:
    """Call cursor-agent CLI with the given prompt.
    
    Args:
        prompt: The prompt to send to cursor-agent
        
    Returns:
        Parsed JSON response or None if failed
    """
    try:
        # Call cursor-agent --model composer-1 --print with the prompt
        result = subprocess.run(
            ["cursor-agent", "--model", "composer-1", "--print", "--output-format", "json", prompt],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )
        
        if result.returncode != 0:
            print(f"Error: cursor-agent failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None
        
        # Parse the JSON response from cursor-agent
        output = result.stdout.strip()
        
        try:
            # cursor-agent returns a wrapper JSON with result field
            wrapper = json.loads(output)
            
            # Extract the actual result content
            if isinstance(wrapper, dict) and "result" in wrapper:
                result_text = wrapper["result"]
                # The result should contain our JSON recommendations
                # Try to extract JSON from the result text
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    # If no JSON found, try parsing the whole result
                    return json.loads(result_text)
            else:
                # Fallback: try parsing the whole output as our expected format
                return wrapper
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from raw output
            json_start = output.find('{')
            json_end = output.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = output[json_start:json_end]
                return json.loads(json_str)
            else:
                raise
            
    except subprocess.TimeoutExpired:
        print("Error: cursor-agent timed out")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON response: {e}")
        print(f"Output: {result.stdout[:500]}")
        return None
    except FileNotFoundError:
        print("Error: cursor-agent not found. Make sure Cursor CLI is installed.")
        return None
    except Exception as e:
        print(f"Error calling cursor-agent: {e}")
        return None


def analyze_project_prompts(
    prompts: List[Dict[str, Any]],
    project_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Analyze prompts for a specific project.
    
    Args:
        prompts: List of prompts from the project
        project_path: Optional project path for context
        
    Returns:
        List of recommendation dictionaries
    """
    if not prompts:
        return []
    
    prompt_text = generate_recommendations_prompt(prompts, scope="project", project_path=project_path)
    response = call_cursor_agent(prompt_text)
    
    if not response:
        return []
    
    recommendations = response.get("recommendations", [])
    
    # Add scope metadata
    for rec in recommendations:
        rec["scope"] = "project"
        rec["project_path"] = project_path
    
    return recommendations


def analyze_cross_project_patterns(
    prompts_by_project: Dict[str, List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Analyze prompts across multiple projects to find global patterns.
    
    Args:
        prompts_by_project: Dictionary mapping project_path to list of prompts
        
    Returns:
        List of recommendation dictionaries for global rules/commands
    """
    # Only analyze if we have prompts from 2+ projects
    if len(prompts_by_project) < 2:
        return []
    
    # Collect sample prompts from each project
    all_prompts = []
    project_summary = []
    
    for project_path, prompts in prompts_by_project.items():
        sample = prompts[:10]  # Sample up to 10 prompts per project
        all_prompts.extend(sample)
        project_summary.append(f"{project_path}: {len(prompts)} prompts")
    
    if not all_prompts:
        return []
    
    # Create a summary prompt
    formatted_prompts = format_prompts_for_analysis(all_prompts, max_prompts=50)
    project_list = "\n".join(project_summary)
    
    prompt = f"""Analyze these prompts from multiple projects and identify patterns that appear across projects. These should be global rules or commands.

Projects analyzed:
{project_list}

{formatted_prompts}

For each cross-project pattern you identify, provide:
1. Type: Either "Rule" (for persistent guidance/instructions) or "Command" (for actions to invoke)
2. Name: A descriptive name for the rule/command
3. Content: The complete rule or command content in proper format
4. Reasoning: Why this pattern warrants global automation

Format your response as JSON with this structure:
{{
  "recommendations": [
    {{
      "type": "Rule" or "Command",
      "name": "descriptive name",
      "content": "full rule/command content",
      "reasoning": "explanation"
    }}
  ]
}}

Focus on patterns that appear consistently across multiple projects, such as:
- Coding style preferences used everywhere
- Common workflows that span projects
- Universal conventions or best practices

Return only valid JSON, no additional text before or after."""
    
    response = call_cursor_agent(prompt)
    
    if not response:
        return []
    
    recommendations = response.get("recommendations", [])
    
    # Add scope metadata
    for rec in recommendations:
        rec["scope"] = "global"
        rec["project_path"] = None
    
    return recommendations

