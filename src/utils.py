"""
Shared utilities for AI e-commerce demos.
All data is fictional for educational purposes only.
"""

import os
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration for AI services."""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    
    @classmethod
    def has_openai_key(cls) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY.strip())


def get_openai_client():
    """
    Get OpenAI client if API key is available.
    Returns None if no API key is configured.
    """
    if not Config.has_openai_key():
        return None
    
    try:
        from openai import OpenAI
        return OpenAI(api_key=Config.OPENAI_API_KEY)
    except ImportError:
        print("Warning: openai package not installed. Install with: pip install openai")
        return None
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        return None


def call_openai_chat(
    prompt: str,
    system_message: str = "You are a helpful assistant.",
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> Optional[str]:
    """
    Call OpenAI chat completion API.
    Returns None if API is not available.
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature or Config.OPENAI_TEMPERATURE,
            max_tokens=max_tokens or Config.OPENAI_MAX_TOKENS
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Warning: OpenAI API call failed: {e}")
        return None


def get_embeddings(texts: List[str]) -> Optional[List[List[float]]]:
    """
    Get embeddings for a list of texts.
    Returns None if API is not available.
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        response = client.embeddings.create(
            model=Config.OPENAI_EMBEDDING_MODEL,
            input=texts
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Warning: OpenAI embeddings call failed: {e}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import numpy as np
    
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    dot_product = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def ensure_dir(directory: str):
    """Create directory if it doesn't exist."""
    os.makedirs(directory, exist_ok=True)


def save_json(data: Any, filepath: str):
    """Save data as JSON file."""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def calculate_sentiment_score(text: str) -> float:
    """
    Simple sentiment scoring based on keywords.
    Returns score between -1.0 (negative) and 1.0 (positive).
    This is a fallback method when API is not available.
    """
    positive_words = {
        'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'love',
        'perfect', 'best', 'awesome', 'beautiful', 'good', 'happy',
        'pleased', 'satisfied', 'recommend', 'quality', 'worth'
    }
    
    negative_words = {
        'terrible', 'awful', 'horrible', 'worst', 'bad', 'poor',
        'disappointed', 'waste', 'broke', 'broken', 'defective',
        'cheap', 'flimsy', 'useless', 'hate', 'never', 'avoid'
    }
    
    text_lower = text.lower()
    words = text_lower.split()
    
    pos_count = sum(1 for word in words if word in positive_words)
    neg_count = sum(1 for word in words if word in negative_words)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total


def print_banner(title: str):
    """Print a formatted banner."""
    border = "=" * 60
    print(f"\n{border}")
    print(f"  {title}")
    print(f"{border}\n")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n--- {title} ---\n")


if __name__ == "__main__":
    # Test configuration
    print_banner("AI E-Commerce Utils - Configuration Test")
    
    print(f"OpenAI API Key configured: {Config.has_openai_key()}")
    print(f"Model: {Config.OPENAI_MODEL}")
    print(f"Embedding Model: {Config.OPENAI_EMBEDDING_MODEL}")
    print(f"Temperature: {Config.OPENAI_TEMPERATURE}")
    print(f"Max Tokens: {Config.OPENAI_MAX_TOKENS}")
    
    if Config.has_openai_key():
        print("\n✓ OpenAI API is configured")
        print("  Demos will use GPT-4 and embeddings for enhanced results")
    else:
        print("\n⚠ OpenAI API key not found")
        print("  Demos will use fallback methods (still functional)")
        print("  To enable API: Add OPENAI_API_KEY to .env file")
