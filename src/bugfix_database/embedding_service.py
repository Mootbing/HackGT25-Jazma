from typing import List
from openai import OpenAI
import os


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""
    
    def __init__(self, api_key: str = None):
        """Initialize the embedding service.
        
        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY env var.
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"  # 1536 dimensions
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [data.embedding for data in response.data]
