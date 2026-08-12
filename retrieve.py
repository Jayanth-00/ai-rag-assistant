import logging
import os
import re
from dataclasses import dataclass, field

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

logger = logging.getLogger("retrieval")

# --- Config flags (env-overridable so each stage can be A/B tested independently) ---
def _env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

USE_HYBRID_SEARCH = _env_bool("USE_HYBRID_SEARCH", True)
USE_RERANKING = _env_bool("USE_RERANKING", True)
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "25"))      # candidates fed to the cross-encoder
FINAL_TOP_N = int(os.getenv("FINAL_TOP_N", "5"))         # default result count
RRF_K = int(os.getenv("RRF_K", "60"))                    # RRF smoothing constant
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "1.0"))     # weight of BM25 list in RRF fusion
CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(name="jayanth_profile")

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


@dataclass
class RetrievalState:
    bm25_index: BM25Okapi | None = None
    chunk_ids: list[str] = field(default_factory=list)
    chunk_texts: dict[str, str] = field(default_factory=dict)
    cross_encoder: CrossEncoder | None = None


_state = RetrievalState()


def build_bm25_index() -> int:
    """Pull all chunks from ChromaDB and build an in-memory BM25 index."""
    records = collection.get(include=["documents"])
    ids, docs = records["ids"], records["documents"]

    _state.chunk_ids = ids
    _state.chunk_texts = dict(zip(ids, docs))
    _state.bm25_index = BM25Okapi([_tokenize(doc) for doc in docs]) if docs else None

    logger.info("BM25 index built over %d chunks", len(ids))
    return len(ids)


def load_cross_encoder() -> CrossEncoder:
    logger.info("Loading cross-encoder model %s ...", CROSS_ENCODER_MODEL)
    _state.cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
    return _state.cross_encoder


def init_retrieval() -> RetrievalState:
    """Build the BM25 index and load the cross-encoder once, at app startup."""
    if USE_HYBRID_SEARCH:
        build_bm25_index()
    if USE_RERANKING:
        load_cross_encoder()
    return _state


def vector_search(question: str, k: int) -> list[tuple[str, float]]:
    """Vector search against ChromaDB. Returns [(chunk_id, distance)] ranked best-first."""
    k = min(k, max(collection.count(), 1))
    query_embedding = model.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    ids = results["ids"][0]
    distances = results["distances"][0]
    # Cache texts so downstream stages don't need another DB round-trip.
    for chunk_id, doc in zip(ids, results["documents"][0]):
        _state.chunk_texts[chunk_id] = doc

    logger.info("Vector search returned %d results", len(ids))
    return list(zip(ids, distances))


def bm25_search(question: str, k: int) -> list[tuple[str, float]]:
    """BM25 search against the in-memory index. Returns [(chunk_id, score)] ranked best-first."""
    if _state.bm25_index is None:
        build_bm25_index()
    if _state.bm25_index is None:  # empty collection
        logger.warning("BM25 index is empty; skipping keyword search")
        return []

    scores = _state.bm25_index.get_scores(_tokenize(question))
    ranked = sorted(zip(_state.chunk_ids, scores), key=lambda pair: pair[1], reverse=True)
    # Score 0 means no term overlap at all -- not a meaningful match.
    ranked = [(chunk_id, score) for chunk_id, score in ranked[:k] if score > 0]

    logger.info("BM25 search returned %d results", len(ranked))
    return ranked


def rrf_fuse(
    vector_results: list[tuple[str, float]],
    bm25_results: list[tuple[str, float]],
    rrf_k: int = RRF_K,
    bm25_weight: float = BM25_WEIGHT,
) -> list[tuple[str, float]]:
    """Merge two ranked lists with Reciprocal Rank Fusion. Returns [(chunk_id, fused_score)]."""
    fused: dict[str, float] = {}
    for rank, (chunk_id, _) in enumerate(vector_results, start=1):
        fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
    for rank, (chunk_id, _) in enumerate(bm25_results, start=1):
        fused[chunk_id] = fused.get(chunk_id, 0.0) + bm25_weight / (rrf_k + rank)

    merged = sorted(fused.items(), key=lambda pair: pair[1], reverse=True)
    logger.info("RRF fusion produced %d unique candidates", len(merged))
    return merged


def rerank(question: str, candidate_ids: list[str], top_n: int) -> list[tuple[str, float]]:
    """Score (query, chunk_text) pairs with the cross-encoder and re-sort. Returns [(chunk_id, score)]."""
    if _state.cross_encoder is None:
        load_cross_encoder()

    pairs = [(question, _state.chunk_texts[chunk_id]) for chunk_id in candidate_ids]
    scores = _state.cross_encoder.predict(pairs)
    reranked = sorted(zip(candidate_ids, scores), key=lambda pair: pair[1], reverse=True)[:top_n]

    logger.info("Cross-encoder reranked %d candidates, keeping top %d", len(candidate_ids), len(reranked))
    return [(chunk_id, float(score)) for chunk_id, score in reranked]


def retrieve(question: str, top_k: int = FINAL_TOP_N):
    """Retrieve the top_k most relevant chunks for a question.

    Same interface as the original vector-only version: returns a Chroma-style
    dict with "ids", "documents" and "distances" (nested lists, one row per query).
    Internally runs hybrid search (vector + BM25 fused via RRF) and cross-encoder
    reranking, each toggleable via env flags.
    """
    # Pull a wider candidate pool when a later stage will narrow it down.
    candidate_k = max(RERANK_TOP_K, top_k) if (USE_HYBRID_SEARCH or USE_RERANKING) else top_k

    vector_results = vector_search(question, candidate_k)
    vector_distances = dict(vector_results)

    if USE_HYBRID_SEARCH:
        bm25_results = bm25_search(question, candidate_k)
        candidates = rrf_fuse(vector_results, bm25_results)
    else:
        candidates = vector_results

    if USE_RERANKING and candidates:
        candidate_ids = [chunk_id for chunk_id, _ in candidates[:RERANK_TOP_K]]
        ranked = rerank(question, candidate_ids, top_n=top_k)
    else:
        ranked = candidates[:top_k]

    final_ids = [chunk_id for chunk_id, _ in ranked]
    logger.info("Returning %d final results", len(final_ids))

    return {
        "ids": [final_ids],
        "documents": [[_state.chunk_texts[chunk_id] for chunk_id in final_ids]],
        # Vector distance where the chunk came through vector search; BM25-only
        # chunks have no distance, so None keeps positions aligned.
        "distances": [[vector_distances.get(chunk_id) for chunk_id in final_ids]],
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    question = "What cloud does Jayanth have experience with?"
    results = retrieve(question, top_k=5)

    print(f"Question: {question}\n")
    docs = results["documents"][0]
    distances = results["distances"][0]

    for i, (doc, dist) in enumerate(zip(docs, distances), start=1):
        dist_label = f"{dist:.4f}" if dist is not None else "n/a (BM25-only)"
        print(f"{i}. (distance: {dist_label}) {doc}")
