"""
Custom embedder that extends Graphiti's OpenAIEmbedder with token limiting.
This ensures that all embedding calls through Graphiti respect token limits.
"""

import logging
from collections.abc import Iterable
from typing import List

from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig

# Import tiktoken with fallback
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

logger = logging.getLogger(__name__)


class TokenLimitedOpenAIEmbedder(OpenAIEmbedder):
    """
    Custom OpenAI embedder that extends Graphiti's OpenAIEmbedder with token limiting.
    This ensures that text is properly truncated before being sent to the OpenAI API.
    """
    
    def __init__(self, config: OpenAIEmbedderConfig | None = None, client=None):
        """Initialize the token-limited embedder."""
        super().__init__(config, client)
        
        # Model-specific token limits
        self.model_token_limits = {
            "text-embedding-3-small": 8191,
            "text-embedding-3-large": 8191,
            "text-embedding-ada-002": 8191
        }
        
        # Get token limit for the current model
        self.max_tokens = self.model_token_limits.get(
            str(self.config.embedding_model), 
            8191  # Default limit
        )
        
        # Initialize tokenizer for accurate token counting
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model(str(self.config.embedding_model))
            except KeyError:
                # Fallback to cl100k_base encoding for unknown models
                logger.warning(f"No tokenizer found for {self.config.embedding_model}, using cl100k_base")
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.tokenizer = None
            logger.warning("tiktoken not available - using character-based estimation for token limiting")
    
    def _truncate_text(self, text: str) -> str:
        """
        Truncate text to fit within model's token limit.
        
        Args:
            text: Text to truncate
        
        Returns:
            Truncated text that fits within token limit
        """
        if not text or not text.strip():
            return text
        
        if self.tokenizer is not None:
            # Use accurate token counting with tiktoken
            tokens = self.tokenizer.encode(text)
            
            # If within limit, return as-is
            if len(tokens) <= self.max_tokens:
                return text
            
            # Truncate tokens and decode back to text
            truncated_tokens = tokens[:self.max_tokens]
            truncated_text = self.tokenizer.decode(truncated_tokens)
            
            logger.warning(f"Text truncated from {len(tokens)} to {len(truncated_tokens)} tokens for embedding")
            return truncated_text
        else:
            # Fallback to character-based estimation (less accurate)
            max_chars = self.max_tokens * 4  # Rough estimation
            if len(text) <= max_chars:
                return text
            
            truncated_text = text[:max_chars]
            logger.warning(f"Text truncated from {len(text)} to {len(truncated_text)} characters for embedding (tiktoken not available)")
            return truncated_text
    
    def _truncate_text_list(self, texts: List[str]) -> List[str]:
        """
        Truncate a list of texts to fit within token limits.
        
        Args:
            texts: List of texts to truncate
        
        Returns:
            List of truncated texts
        """
        return [self._truncate_text(text) for text in texts]
    
    async def create(
        self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]
    ) -> list[float]:
        """
        Create embeddings with token limiting.
        
        Args:
            input_data: Input data to embed
        
        Returns:
            Embedding vector
        """
        # Handle string input
        if isinstance(input_data, str):
            truncated_text = self._truncate_text(input_data)
            return await super().create(truncated_text)
        
        # Handle list of strings
        elif isinstance(input_data, list) and all(isinstance(item, str) for item in input_data):
            truncated_texts = self._truncate_text_list(input_data)
            return await super().create(truncated_texts)
        
        # For other types (token lists), pass through as-is
        else:
            return await super().create(input_data)
    
    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        """
        Create batch embeddings with token limiting.
        
        Args:
            input_data_list: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        # Truncate all texts in the batch
        truncated_texts = self._truncate_text_list(input_data_list)
        
        # Call parent's create_batch method
        return await super().create_batch(truncated_texts)


def create_token_limited_embedder(
    api_key: str,
    embedding_model: str = "text-embedding-3-small",
    embedding_dim: int = 1536,
    base_url: str | None = None
) -> TokenLimitedOpenAIEmbedder:
    """
    Factory function to create a token-limited embedder.
    
    Args:
        api_key: OpenAI API key
        embedding_model: Embedding model name
        embedding_dim: Embedding dimensions
        base_url: Base URL for API calls
    
    Returns:
        TokenLimitedOpenAIEmbedder instance
    """
    config = OpenAIEmbedderConfig(
        api_key=api_key,
        embedding_model=embedding_model,
        embedding_dim=embedding_dim,
        base_url=base_url
    )
    
    return TokenLimitedOpenAIEmbedder(config=config)
