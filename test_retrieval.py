"""Sanity-check the retrieval pipeline stage by stage.

Run directly:      python test_retrieval.py ["your question here"]
Or under pytest:   pytest test_retrieval.py -s
"""
import logging
import sys

from retrieve import (
    RERANK_TOP_K,
    bm25_search,
    rerank,
    retrieve,
    rrf_fuse,
    vector_search,
    _state,
)

DEFAULT_QUESTION = "What cloud does Jayanth have experience with?"


def _print_stage(title: str, rows: list[tuple[str, float]], score_label: str):
    print(f"\n--- {title} ---")
    if not rows:
        print("  (no results)")
        return
    for i, (chunk_id, score) in enumerate(rows, start=1):
        text = _state.chunk_texts.get(chunk_id, "<text not cached>")
        print(f"  {i}. [{chunk_id}] {score_label}={score:.4f}  {text}")


def run_pipeline_stages(question: str, top_k: int = 5):
    print(f"Question: {question}")

    vector_results = vector_search(question, RERANK_TOP_K)
    _print_stage("Vector-only (ChromaDB)", vector_results, "distance")

    bm25_results = bm25_search(question, RERANK_TOP_K)
    _print_stage("BM25-only (keyword)", bm25_results, "bm25_score")

    fused = rrf_fuse(vector_results, bm25_results)
    _print_stage("Fused (RRF)", fused, "rrf_score")

    reranked = rerank(question, [cid for cid, _ in fused[:RERANK_TOP_K]], top_n=top_k)
    _print_stage("Final (cross-encoder reranked)", reranked, "ce_score")

    return vector_results, bm25_results, fused, reranked


def test_full_pipeline():
    vector_results, bm25_results, fused, reranked = run_pipeline_stages(DEFAULT_QUESTION)

    assert vector_results, "vector search returned nothing"
    assert fused, "RRF fusion returned nothing"
    assert reranked, "reranking returned nothing"
    # Fused list must be deduplicated.
    fused_ids = [cid for cid, _ in fused]
    assert len(fused_ids) == len(set(fused_ids)), "fused list contains duplicates"

    # The public interface must keep its original Chroma-style shape.
    results = retrieve(DEFAULT_QUESTION, top_k=3)
    assert set(results) >= {"documents", "distances"}
    assert len(results["documents"][0]) <= 3
    assert len(results["documents"][0]) == len(results["distances"][0])
    print("\nretrieve() interface check passed:", results["documents"][0])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    question = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUESTION
    run_pipeline_stages(question)
