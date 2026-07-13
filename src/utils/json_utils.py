import json
import re
from typing import List

from pydantic import BaseModel, ValidationError


def extract_json_array(text: str) -> List[str]:
    """
    Extracts a JSON array of strings from a given text.
    Safely finds the outermost JSON array boundaries.
    """
    # re.DOTALL allows the dot to match newlines.
    # Finds the first open bracket, then grabs everything up to a closing bracket.
    match = re.search(r'\[.*\]', text, re.DOTALL)

    if match:
        try:
            result = json.loads(match.group(0))
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return []


def parse_structured_output(text: str, model_class: type[BaseModel]) -> BaseModel:
    """
    Parses a JSON string into a Pydantic model instance.
    Safely finds the outermost JSON object boundaries.
    """
    # re.DOTALL allows the dot to match newlines.
    # Finds the first open brace, then grabs everything up to a closing brace.
    match = re.search(r'\{.*\}', text, re.DOTALL)

    if match:
        try:
            json_str = match.group(0)
            return model_class.model_validate_json(json_str)
        except (ValidationError, ValueError):
            # ValidationError handles Pydantic mismatches; ValueError handles basic JSON syntax issues
            pass

    raise ValueError(f"No valid JSON object matching {model_class.__name__} found.")


def parse_structured_list(text: str, model_class: type[BaseModel]) -> List[BaseModel]:
    """
    Parses a JSON array of objects into a list of Pydantic model instances.
    Safely finds the outermost JSON array boundaries.
    """
    match = re.search(r'\[.*\]', text, re.DOTALL)

    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return [model_class.model_validate(item) for item in data]
        except (ValidationError, json.JSONDecodeError, ValueError):
            pass

    raise ValueError(f"No valid JSON array of {model_class.__name__} found.")
