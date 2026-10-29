import os
import math
import json
import logging
import hashlib
from typing import List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard embedding vector dimension for Google text-embedding-004
EMBEDDING_DIM = 768


def get_embedding_model_name() -> str:
    return os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004").strip()


def is_fallback_embedding_active() -> bool:
    api_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
    return not api_key or "your_" in api_key.lower() or not api_key.startswith("AIzaSy")


def generate_deterministic_fallback_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Generates a high-quality normalized float32 pseudo-semantic vector embedding
    for offline testing, development without external keys, and air-gapped CI environments.
    Uses MD5/SHA256 sliding hash buckets with L2 normalization to ensure non-zero cosine similarity
    for overlapping tokens and strict unit length.
    """
    if not text:
        return [0.0] * dim

    vec = [0.0] * dim
    words = text.lower().split()
    
    # 1. Bag of words hash projection
    for w_idx, word in enumerate(words):
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx1 = h % dim
        idx2 = (h >> 16) % dim
        idx3 = (h >> 32) % dim
        sign = 1.0 if ((h >> 48) % 2 == 0) else -1.0
        
        weight = 1.0 / math.sqrt(w_idx + 1)
        vec[idx1] += sign * weight
        vec[idx2] += (sign * -0.5) * weight
        vec[idx3] += (sign * 0.25) * weight

    # 2. Character n-gram projection for subword semantic similarity
    for i in range(len(text) - 3):
        ngram = text[i:i + 4].lower()
        nh = int(hashlib.sha256(ngram.encode("utf-8")).hexdigest()[:8], 16)
        vec[nh % dim] += 0.15

    # 3. L2 Unit Normalization (sum of squares = 1.0)
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-9:
        vec = [round(x / norm, 6) for x in vec]
    else:
        vec[0] = 1.0

    return vec


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generates 768-dimensional vector embeddings for a list of text strings.
    Attempts Google Gemini API (via google-genai SDK or REST API) if GEMINI_API_KEY is configured.
    Seamlessly falls back to deterministic vector projection when running in test/mock/offline mode.
    """
    if not texts:
        return []

    api_key = (settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")).strip()
    model_name = get_embedding_model_name()

    # If missing or placeholder or non-Google AI Studio key, use resilient deterministic adapter
    if not api_key or "your_" in api_key.lower() or not api_key.startswith("AIzaSy"):
        logger.debug("Generating embeddings via deterministic offline adapter.")
        return [generate_deterministic_fallback_embedding(t) for t in texts]

    # Attempt official google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Batch within 100 items per request
        batch_size = 50
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            resp = client.models.embed_content(
                model=model_name,
                contents=batch,
            )
            if hasattr(resp, "embeddings") and resp.embeddings:
                for emb in resp.embeddings:
                    values = getattr(emb, "values", None) or emb
                    if hasattr(values, "tolist"):
                        values = values.tolist()
                    all_embeddings.append(list(values))
            else:
                raise ValueError("SDK embed_content returned no embeddings.")

        if len(all_embeddings) == len(texts):
            return all_embeddings

    except Exception as e:
        logger.warning(f"Google GenAI SDK embedding failed: {e}. Trying REST endpoint fallback.")

    # REST endpoint fallback via httpx
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:batchEmbedContents?key={api_key}"
        requests_payload = [
            {"model": f"models/{model_name}", "content": {"parts": [{"text": t}]}}
            for t in texts
        ]
        with httpx.Client(timeout=30.0) as http_client:
            resp = http_client.post(url, json={"requests": requests_payload})
            if resp.status_code == 200:
                data = resp.json()
                embeddings_data = data.get("embeddings", [])
                if len(embeddings_data) == len(texts):
                    return [item["values"] for item in embeddings_data]
            else:
                logger.warning(f"REST batchEmbedContents returned status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.warning(f"REST embedding gateway encountered error: {e}")

    # Resilient fallback
    logger.info("Falling back to deterministic local vector embedding generation.")
    return [generate_deterministic_fallback_embedding(t) for t in texts]


def embed_single_query(query: str) -> List[float]:
    """
    Embeds a single search query string.
    """
    res = embed_texts([query])
    if res and len(res) > 0:
        return res[0]
    return generate_deterministic_fallback_embedding(query)

