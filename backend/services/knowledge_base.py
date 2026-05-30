"""
Knowledge Base using local Sentence Transformers embeddings + NumPy cosine similarity.
Completely free, works offline, no API quota issues.
"""

import json
import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent.parent / "data"
KB_STORE_PATH = Path(__file__).parent.parent / "kb_store.pkl"

# Loads once, small model (~90MB), downloads automatically on first run
_model = SentenceTransformer("all-MiniLM-L6-v2")

_kb: list[dict] = []
_kb_loaded = False


def _get_embedding(text: str) -> np.ndarray:
    return _model.encode(text, convert_to_numpy=True)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def _load_kb():
    global _kb, _kb_loaded
    if _kb_loaded:
        return

    if KB_STORE_PATH.exists():
        with open(KB_STORE_PATH, "rb") as f:
            _kb = pickle.load(f)
        print(f"[KB] Loaded {len(_kb)} incidents from cache.")
    else:
        _seed_incidents()

    _kb_loaded = True


def _seed_incidents():
    global _kb
    with open(DATA_DIR / "incidents.json") as f:
        incidents = json.load(f)

    print(f"[KB] Embedding {len(incidents)} incidents locally (one-time setup)...")
    _kb = []
    for inc in incidents:
        text = (
            f"Incident: {inc['title']}\n"
            f"Service: {inc['service']}\n"
            f"Severity: {inc['severity']}\n"
            f"Root Cause: {inc['root_cause']}\n"
            f"Resolution: {inc['resolution']}\n"
            f"Tags: {', '.join(inc['tags'])}"
        )
        embedding = _get_embedding(text)
        _kb.append({
            "meta": {
                "id": inc["id"],
                "title": inc["title"],
                "service": inc["service"],
                "severity": inc["severity"],
                "root_cause": inc["root_cause"],
                "resolution": inc["resolution"],
                "tags": ", ".join(inc["tags"])
            },
            "embedding": embedding
        })

    with open(KB_STORE_PATH, "wb") as f:
        pickle.dump(_kb, f)
    print(f"[KB] Seeded and cached {len(_kb)} incidents.")


def search_similar_incidents(query: str, n_results: int = 3) -> list[dict]:
    _load_kb()
    query_emb = _get_embedding(query)

    scored = []
    for item in _kb:
        score = _cosine_similarity(query_emb, item["embedding"])
        scored.append((score, item["meta"]))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {**meta, "relevance_score": round(score, 3)}
        for score, meta in scored[:n_results]
    ]


def add_incident_to_kb(incident: dict):
    _load_kb()
    text = (
        f"Incident: {incident['title']}\n"
        f"Service: {incident['service']}\n"
        f"Severity: {incident['severity']}\n"
        f"Root Cause: {incident['root_cause']}\n"
        f"Resolution: {incident['resolution']}"
    )
    embedding = _get_embedding(text)
    _kb.append({
        "meta": {
            "id": incident["id"],
            "title": incident["title"],
            "service": incident["service"],
            "severity": incident["severity"],
            "root_cause": incident["root_cause"],
            "resolution": incident["resolution"],
            "tags": incident.get("tags", "")
        },
        "embedding": embedding
    })
    with open(KB_STORE_PATH, "wb") as f:
        pickle.dump(_kb, f)
    print(f"[KB] Added {incident['id']} to knowledge base.")