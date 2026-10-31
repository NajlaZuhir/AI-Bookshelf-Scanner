"""Generate normalized semantic embeddings for recommendation inputs."""

from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

def generate_embeddings(
    texts: list[str],
    model: SentenceTransformer,
) -> np.ndarray:
    """Generate normalized semantic embeddings."""

    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
