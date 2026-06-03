import logging
import re
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import settings
from app.parsers.code_parser import ParsedChunk, add_context_header

logger = logging.getLogger(__name__)

_client: chromadb.PersistentClient | None = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DB_PATH),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized")
    return _client


def _collection_name(repo_id: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9-]", "-", f"repo-{repo_id}")
    name = re.sub(r"-+", "-", name).strip("-").lower()
    return name[:63] if len(name) > 63 else name


def store_chunks(
    repo_id: str,
    chunks: List[ParsedChunk],
    embeddings: List[List[float]],
) -> int:
    if not chunks:
        return 0

    client = get_client()
    col_name = _collection_name(repo_id)

    try:
        client.delete_collection(col_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=col_name,
        metadata={"repo_id": repo_id, "hnsw:space": "cosine"},
    )

    batch_size = 400
    stored = 0

    for start in range(0, len(chunks), batch_size):
        end = min(start + batch_size, len(chunks))
        batch = chunks[start:end]
        batch_embs = embeddings[start:end]

        ids = []
        for i, c in enumerate(batch):
            raw_id = f"{repo_id}_{c.file_path}_{c.chunk_type}_{c.name or ''}_{start + i}"
            ids.append(re.sub(r"[^a-zA-Z0-9_:-]", "_", raw_id)[:512])

        documents = [add_context_header(c) for c in batch]
        metadatas = [
            {
                "file_path": c.file_path,
                "chunk_type": c.chunk_type,
                "name": c.name or "",
                "language": c.language,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "parent_class": c.parent_class or "",
                "repo_id": repo_id,
            }
            for c in batch
        ]

        collection.add(ids=ids, embeddings=batch_embs, documents=documents, metadatas=metadatas)
        stored += len(batch)

    logger.info(f"Stored {stored} chunks for repo {repo_id}")
    return stored


def retrieve_chunks(
    repo_id: str,
    query_embedding: List[float],
    top_k: int = settings.TOP_K_RESULTS,
    where: Optional[Dict] = None,
) -> List[Dict]:
    client = get_client()
    col_name = _collection_name(repo_id)

    try:
        collection = client.get_collection(col_name)
    except Exception:
        raise ValueError(f"Repository '{repo_id}' not indexed. Please process it first.")

    count = collection.count()
    if count == 0:
        raise ValueError(f"Repository '{repo_id}' has no indexed chunks.")

    actual_k = min(top_k, count)
    kwargs: Dict = dict(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        include=["documents", "metadatas", "distances"],
    )
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        output.append({
            "content": doc,
            "file_path": meta.get("file_path", ""),
            "chunk_type": meta.get("chunk_type", ""),
            "function_name": meta.get("name", ""),
            "language": meta.get("language", ""),
            "start_line": meta.get("start_line", 0),
            "end_line": meta.get("end_line", 0),
            "parent_class": meta.get("parent_class", ""),
            "score": round(1.0 - dist, 4),
        })

    return output


def collection_exists(repo_id: str) -> bool:
    try:
        col = get_client().get_collection(_collection_name(repo_id))
        return col.count() > 0
    except Exception:
        return False


def delete_collection(repo_id: str) -> None:
    try:
        get_client().delete_collection(_collection_name(repo_id))
    except Exception:
        pass
