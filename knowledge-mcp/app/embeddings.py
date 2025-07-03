import os
import asyncio
from typing import List
import httpx

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))

async def generate_embedding_openai(text: str) -> List[float]:
    """Generate embeddings using OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "input": text,
                "model": EMBEDDING_MODEL
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise ValueError(f"OpenAI API error: {response.status_code} - {response.text}")
        
        data = response.json()
        return data["data"][0]["embedding"]

async def generate_embedding(text: str) -> List[float]:
    """
    Generate embeddings for text.
    Uses OpenAI if API key is available, otherwise uses mock embeddings.
    """
    if OPENAI_API_KEY:
        try:
            return await generate_embedding_openai(text)
        except Exception as e:
            print(f"OpenAI embedding failed: {e}")
            raise e

async def generate_embeddings_batch(texts: List[str], batch_size: int = 10) -> List[List[float]]:
    """Generate embeddings for multiple texts in batches."""
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = await asyncio.gather(
            *[generate_embedding(text) for text in batch]
        )
        embeddings.extend(batch_embeddings)
    
    return embeddings 