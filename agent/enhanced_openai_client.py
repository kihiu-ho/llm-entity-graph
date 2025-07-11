"""
Enhanced OpenAI client for Graphiti that handles JSON parsing issues.
This client wraps the standard Graphiti OpenAI client and adds robust JSON parsing.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError

from graphiti_core.llm_client.openai_client import OpenAIClient
from graphiti_core.llm_client.config import LLMConfig, ModelSize
from graphiti_core.prompts.models import Message
from graphiti_core.llm_client.errors import RefusalError

logger = logging.getLogger(__name__)


class EnhancedOpenAIClient(OpenAIClient):
    """
    Enhanced OpenAI client that handles common JSON parsing issues.
    
    This client extends the standard Graphiti OpenAI client to handle:
    - Markdown code block wrapping (```json ... ```)
    - Table-formatted responses
    - Extra whitespace and formatting issues
    - Malformed JSON responses
    """
    
    def __init__(self, config: LLMConfig | None = None, cache: bool = False):
        """Initialize the enhanced client."""
        super().__init__(config, cache)

        # Check if we're using a non-OpenAI API that doesn't support structured parsing
        self.supports_structured_parsing = True
        if config and config.base_url:
            # Common non-OpenAI APIs that don't support structured parsing
            non_openai_domains = ['chataiapi.com', 'api.groq.com', 'api.anthropic.com']
            if any(domain in config.base_url for domain in non_openai_domains):
                self.supports_structured_parsing = False
                logger.info(f"Detected non-OpenAI API ({config.base_url}), disabling structured parsing")

        logger.info("Enhanced OpenAI client initialized with robust JSON parsing")
    
    def _clean_json_response(self, text: str) -> str:
        """
        Clean and extract JSON from various response formats.
        
        Args:
            text: Raw response text from LLM
        
        Returns:
            Cleaned JSON string
        """
        if not text or not text.strip():
            return "{}"
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Handle markdown code blocks
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]   # Remove ```
        
        if text.endswith("```"):
            text = text[:-3]  # Remove trailing ```
        
        # Handle table format responses
        if "|" in text and "Entity" in text:
            logger.warning("Detected table format response, attempting to convert to JSON")
            return self._convert_table_to_json(text)
        
        # Handle different JSON formats
        if text.startswith('['):
            # Handle array format
            json_end = text.rfind(']') + 1
            if json_end > 0:
                text = text[:json_end]
        elif text.startswith('{'):
            # Handle single object format
            json_end = text.rfind('}') + 1
            if json_end > 0:
                text = text[:json_end]
        else:
            # Look for JSON content within the text
            json_start = text.find('{')
            if json_start >= 0:
                # Check if we have multiple objects or an array
                if '{"entity_name":' in text:
                    # This looks like entity extraction response
                    # Keep the entire text for processing in _fix_common_json_issues
                    pass
                else:
                    json_end = text.rfind('}') + 1
                    if json_end > json_start:
                        text = text[json_start:json_end]
        
        # Clean up common formatting issues
        text = text.strip()
        
        # Remove any remaining markdown artifacts
        text = re.sub(r'^```.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n```$', '', text)
        
        return text
    
    def _convert_table_to_json(self, table_text: str) -> str:
        """
        Convert table format response to JSON.
        
        Args:
            table_text: Table formatted text
        
        Returns:
            JSON string representation
        """
        try:
            lines = table_text.strip().split('\n')
            entities = []
            
            for line in lines:
                if '|' in line and 'Entity' not in line and '---' not in line:
                    parts = [part.strip() for part in line.split('|') if part.strip()]
                    if len(parts) >= 3:
                        # Assume format: | Name | Type | ... |
                        entity_name = parts[0]
                        entity_type = parts[1] if len(parts) > 1 else "Unknown"
                        
                        # Map entity types
                        if entity_type.lower() in ['person', 'people', '1']:
                            entity_type_id = 1
                        elif entity_type.lower() in ['company', 'organization', '2']:
                            entity_type_id = 2
                        else:
                            entity_type_id = 1  # Default to person
                        
                        entities.append({
                            "entity_name": entity_name,
                            "entity_type": entity_type,
                            "entity_type_id": entity_type_id
                        })
            
            return json.dumps(entities)
            
        except Exception as e:
            logger.warning(f"Failed to convert table to JSON: {e}")
            return "[]"
    
    def _validate_and_fix_json(self, json_str: str, response_model: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
        """
        Validate and attempt to fix JSON structure.
        
        Args:
            json_str: JSON string to validate
            response_model: Expected Pydantic model for validation
        
        Returns:
            Validated JSON as dictionary
        """
        try:
            # First attempt: parse as-is
            data = json.loads(json_str)
            
            # If we have a response model, validate against it
            if response_model:
                try:
                    validated = response_model.model_validate(data)
                    return validated.model_dump()
                except ValidationError as e:
                    logger.warning(f"Response model validation failed: {e}")
                    # Continue with unvalidated data
            
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}, attempting to fix")
            logger.debug(f"Original JSON string: {repr(json_str)}")

            # Attempt to fix common JSON issues
            fixed_json = self._fix_common_json_issues(json_str)
            logger.debug(f"Fixed JSON string: {repr(fixed_json)}")

            try:
                data = json.loads(fixed_json)
                logger.info("Successfully fixed JSON parsing issue")
                return data
            except json.JSONDecodeError as fix_error:
                logger.error(f"Could not fix JSON: {fixed_json}")
                logger.error(f"Fix error: {fix_error}")

                # Try one more approach: extract individual JSON objects
                try:
                    objects = self._extract_json_objects(json_str)
                    if objects:
                        logger.info(f"Extracted {len(objects)} JSON objects")
                        return objects
                except Exception as extract_error:
                    logger.error(f"Object extraction failed: {extract_error}")

                # Return empty structure based on response model
                if response_model:
                    try:
                        # Create empty instance of the model
                        empty_instance = response_model()
                        return empty_instance.model_dump()
                    except Exception:
                        pass

                return {}
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """
        Fix common JSON formatting issues.

        Args:
            json_str: Malformed JSON string

        Returns:
            Fixed JSON string
        """
        # Handle case where we have multiple JSON objects without array brackets
        if '{"entity_name":' in json_str and not json_str.strip().startswith('['):
            # Split by lines and find JSON objects
            lines = json_str.strip().split('\n')
            json_objects = []

            for line in lines:
                line = line.strip()
                if line and (line.startswith('{') or '{"entity_name":' in line):
                    # Remove trailing comma if present
                    if line.endswith(','):
                        line = line[:-1]
                    json_objects.append(line)

            if json_objects:
                # Join objects into a proper array
                json_str = '[' + ','.join(json_objects) + ']'

        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix unquoted keys (but be careful not to break already quoted keys)
        json_str = re.sub(r'(\w+):', r'"\1":', json_str)
        # Fix double-quoted keys that got double-quoted
        json_str = re.sub(r'""(\w+)"":', r'"\1":', json_str)

        # Fix single quotes to double quotes
        json_str = json_str.replace("'", '"')

        # Remove any non-JSON content at the end
        json_str = re.sub(r'[^}\]]*$', '', json_str)

        # Handle incomplete JSON arrays (missing closing bracket)
        if json_str.strip().startswith('[') and not json_str.strip().endswith(']'):
            # Count opening and closing brackets
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            if open_brackets > close_brackets:
                json_str = json_str.rstrip() + ']'

        return json_str

    def _extract_json_objects(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract individual JSON objects from malformed text.

        Args:
            text: Text containing JSON objects

        Returns:
            List of extracted JSON objects
        """
        objects = []

        # Look for patterns like {"entity_name": "...", "entity_type_id": ...}
        pattern = r'\{"entity_name":\s*"([^"]+)",\s*"entity_type_id":\s*(\d+)\}'
        matches = re.findall(pattern, text)

        for name, type_id in matches:
            objects.append({
                "entity_name": name,
                "entity_type_id": int(type_id)
            })

        return objects

    async def _generate_response(
        self,
        messages: List[Message],
        response_model: Optional[Type[BaseModel]] = None,
        max_tokens: int = 2000,
        model_size: ModelSize = ModelSize.medium,
    ) -> Dict[str, Any]:
        """
        Generate response with enhanced JSON parsing.
        
        Args:
            messages: List of messages for the conversation
            response_model: Expected response model
            max_tokens: Maximum tokens for response
            model_size: Model size to use
        
        Returns:
            Parsed response as dictionary
        """
        # Skip structured parsing for non-OpenAI APIs
        if not self.supports_structured_parsing:
            logger.debug("Using enhanced parsing directly (structured parsing disabled)")
        else:
            try:
                # First try the standard structured parsing
                return await super()._generate_response(messages, response_model, max_tokens, model_size)

            except Exception as e:
                logger.warning(f"Structured parsing failed: {e}, falling back to enhanced parsing")

        # Fall back to manual parsing with our enhanced logic
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            # Use regular chat completion without structured parsing
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=max_tokens or self.max_tokens,
            )

            # Extract content
            content = response.choices[0].message.content

            if not content:
                logger.warning("Empty response from LLM")
                return {}

            logger.debug(f"Raw LLM response: {content}")

            # Clean and parse JSON
            cleaned_json = self._clean_json_response(content)
            logger.debug(f"Cleaned JSON: {cleaned_json}")

            # Validate and return
            result = self._validate_and_fix_json(cleaned_json, response_model)
            logger.info("Successfully parsed response with enhanced parsing")

            return result

        except Exception as fallback_error:
            logger.error(f"Enhanced parsing also failed: {fallback_error}")
            if self.supports_structured_parsing:
                logger.error(f"Original structured parsing error: {e}")

            # Return empty structure as last resort
            if response_model:
                try:
                    empty_instance = response_model()
                    return empty_instance.model_dump()
                except Exception:
                    pass

            return {}


def create_enhanced_openai_client(
    api_key: str,
    model: str = "gpt-4o-mini",
    base_url: Optional[str] = None,
    cache: bool = False
) -> EnhancedOpenAIClient:
    """
    Factory function to create an enhanced OpenAI client.

    Args:
        api_key: OpenAI API key
        model: Model name to use
        base_url: Base URL for API calls
        cache: Whether to enable caching

    Returns:
        EnhancedOpenAIClient instance
    """
    config = LLMConfig(
        api_key=api_key,
        model=model,
        base_url=base_url
    )

    return EnhancedOpenAIClient(config=config, cache=cache)
