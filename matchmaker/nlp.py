import re
from sentence_transformers import SentenceTransformer
import numpy as np

_MODEL = None
def get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _MODEL

def normalize_text(t: str) -> str:
    if not t:
        return ""
    t = str(t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t

def embed(texts):
    m = get_model()
    embs = m.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return np.asarray(embs, dtype="float32")