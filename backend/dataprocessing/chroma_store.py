import os
import threading
from pathlib import Path

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

CHROMA_HOST = (os.getenv("CHROMA_HOST") or "").strip()
CHROMA_PORT = int(os.getenv("CHROMA_PORT") or 8000)

_client = None   # service that talks to chromadb
_lock = threading.Lock()


def get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                if not CHROMA_HOST:
                    raise RuntimeError("CHROMA_HOST is not set")
                print(f"Chroma HTTP client -> {CHROMA_HOST}:{CHROMA_PORT}")
                _client = chromadb.HttpClient(
                    host=CHROMA_HOST, port=CHROMA_PORT, settings=Settings(
                        anonymized_telemetry=False
                    )
                )
    return _client


def get_collection(collection_name):
    return get_client().get_or_create_collection(
        name=collection_name
    )


def save_vector(chunks, embeddings, collection_name, source_id, title=None):

    # safety checks
    if not chunks:
        raise ValueError("No chunks to store")

    if len(chunks) != len(embeddings):
        raise ValueError(
            f"chunks/embeddings mismatch: {len(chunks)} vs {len(embeddings)}"
        )

    collection = get_collection(collection_name)

    delete_document(collection_name, source_id)
    
    # Create unique IDs
    ids = [
        f"{source_id}::{i}"
        for i in range(len(chunks))   
    ]    


   
    metadatas = [
        {
            "source_id": str(source_id),
            "title": title or str(source_id),
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        for i in range(len(chunks))
    ]  

    # Store/update vectors
    collection.upsert(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=ids,
        metadatas=metadatas,
    )

    print(
        f"Stored {len(chunks)} chunks for "
        f"'{title or source_id}' in '{collection_name}'"
    )

    return collection



def delete_document(collection_name, source_id):
    """Drop every chunk belonging to one source_id."""
    try:
        get_collection(collection_name).delete(
            where={"source_id": str(source_id)}
        )
    except Exception as error:
        print("Delete-by-source failed (continuing):", error)