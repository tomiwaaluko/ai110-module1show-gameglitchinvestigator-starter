"""
RAG Retriever: loads strategy documents into ChromaDB and provides
semantic similarity search for the AI coach agent.
"""

import os

import chromadb
from chromadb.utils import embedding_functions


_collection = None
_fallback_docs = None


def _load_documents() -> list[dict]:
    """Load all documents from the data/ directory."""
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    documents = []

    sources = [
        ("strategy_guide.txt", "strategy"),
        ("debugging_patterns.txt", "debugging"),
        ("binary_search_theory.txt", "theory"),
    ]

    for filename, source_type in sources:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
        for i, chunk in enumerate(chunks):
            documents.append(
                {
                    "id": f"{source_type}_{i}",
                    "text": chunk,
                    "source": filename,
                    "source_type": source_type,
                }
            )

    return documents


def _get_fallback_docs() -> list[dict]:
    """Return loaded documents for keyword fallback retrieval."""
    global _fallback_docs
    if _fallback_docs is None:
        _fallback_docs = _load_documents()
    return _fallback_docs


def _get_collection():
    """Initialize ChromaDB collection with documents if not already done."""
    global _collection
    if _collection is not None:
        return _collection

    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.Client()
    _collection = client.create_collection(
        name="game_strategy",
        embedding_function=embedding_fn,
        get_or_create=True,
    )

    docs = _load_documents()
    if docs and _collection.count() == 0:
        _collection.add(
            ids=[d["id"] for d in docs],
            documents=[d["text"] for d in docs],
            metadatas=[{"source": d["source"], "type": d["source_type"]} for d in docs],
        )

    return _collection


def _keyword_retrieve(query: str, n_results: int) -> list[dict]:
    """Small deterministic fallback if Chroma's embedding model is unavailable."""
    terms = {term.lower().strip(".,:;!?()[]") for term in query.split() if len(term) > 2}
    scored = []
    for doc in _get_fallback_docs():
        text = doc["text"].lower()
        score = sum(1 for term in terms if term in text)
        scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    output = []
    for score, doc in scored[: max(1, n_results)]:
        output.append(
            {
                "text": doc["text"],
                "source": doc["source"],
                "distance": 1.0 / (score + 1),
            }
        )
    return output


def retrieve(query: str, n_results: int = 3) -> list[dict]:
    """
    Retrieve the top-n most relevant document chunks for a given query.

    Returns list of dicts with keys: text, source, distance.
    Lower distance = more relevant.
    """
    try:
        collection = _get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, 10),
        )

        output = []
        if results and results["documents"]:
            for i, doc_text in enumerate(results["documents"][0]):
                output.append(
                    {
                        "text": doc_text,
                        "source": results["metadatas"][0][i].get("source", "unknown"),
                        "distance": results["distances"][0][i]
                        if results.get("distances")
                        else 0.0,
                    }
                )
        return output

    except Exception:
        return _keyword_retrieve(query, n_results)


def get_document_count() -> int:
    """Return number of documents currently indexed."""
    try:
        return _get_collection().count()
    except Exception:
        return len(_get_fallback_docs())
