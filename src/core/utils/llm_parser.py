# MDSAPP/core/utils/llm_parser.py

import logging
import json
import re  # Importeer de regex module
from typing import Dict, Any, Type
from pydantic import BaseModel, ValidationError
from google.generativeai import GenerativeModel

logger = logging.getLogger(__name__)

def _extract_json_from_string(text: str) -> str:
    """
    Extracts a JSON object from a string, which might be wrapped in markdown.
    Handles ```json ... ``` and ``` ... ``` blocks.
    """
    # Zoek naar een JSON markdown blok
    match = re.search(r"```(json)?\n(.*?)\n```", text, re.DOTALL | re.IGNORECASE)
    if match:
        # Groep 2 bevat de JSON content
        return match.group(2).strip()
    # Als er geen markdown blok is, ga er dan vanuit dat de hele string JSON is
    return text.strip()

async def parse_llm_json_output(
    json_string: str, 
    pydantic_model: Type[BaseModel], 
    llm_model: GenerativeModel
) -> Dict[str, Any]:
    """
    Parses a JSON string from LLM output, validates it with a Pydantic model,
    and attempts to self-correct if parsing fails.
    """
    try:
        # Poging 1: Extraheer en parse de JSON
        clean_json_string = _extract_json_from_string(json_string)
        data = json.loads(clean_json_string)
        pydantic_model(**data)
        logger.info(f"Successfully parsed and validated JSON for model {pydantic_model.__name__}.")
        return data
    except (json.JSONDecodeError, ValidationError) as e:
        logger.warning(f"Initial JSON parsing/validation failed for {pydantic_model.__name__}: {e}. Attempting self-correction.")
        if isinstance(e, ValidationError):
            logger.warning(f"Pydantic validation errors: {e.errors()}")

        # Gebruik de originele, mogelijk 'vuile' json_string in de correctie-prompt
        error_details = e.errors() if isinstance(e, ValidationError) else str(e)
        correction_prompt = (
            f"The following JSON output is invalid. Please correct it and return only the valid JSON object. "
            f"Do not include any explanatory text or markdown. The specific errors were: {error_details}\n\n"
            f"Invalid JSON:\n```json\n{json_string}\n```")

        logger.info(f"Self-correction prompt sent to LLM...")
        response = await llm_model.generate_content_async([correction_prompt])
        corrected_json_string = response.text
        logger.info(f"Raw response from self-correction LLM: {corrected_json_string}")

        try:
            # Poging 2: Extraheer en parse de gecorrigeerde JSON
            final_json_string = _extract_json_from_string(corrected_json_string)
            data = json.loads(final_json_string)
            pydantic_model(**data)
            logger.info(f"Successfully parsed and validated JSON for model {pydantic_model.__name__} after self-correction.")
            return data
        except (json.JSONDecodeError, ValidationError) as final_e:
            logger.error(f"Final JSON parsing/validation failed after self-correction: {final_e}")
            error_message = f"Failed to parse LLM output for {pydantic_model.__name__} even after self-correction. Final attempt content: '{final_json_string}'"
            raise ValueError(error_message) from final_e