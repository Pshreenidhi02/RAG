from dataprocessing.parser import parse_file
from dataprocessing.clean_text import clean_text
from dataprocessing.chunking import chunk_text
from dataprocessing.embedding import embedding_model
from dataprocessing.identity import default_source_id
from dataprocessing.chroma_store import save_vector

from pathlib import Path


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 250
COLLECTION_NAME = "my_selectiva_collection"

def process_file(file_path, title=None, source_id=None):
    print(f"Processing: {file_path}")
    
    # step 1
    text = parse_file(file_path)

    #step 2
    cleaned_text = clean_text(text)

    #step 3
    chunks = chunk_text(cleaned_text, max_chars=CHUNK_SIZE, overlap_chars=CHUNK_OVERLAP)

    #step 4
    embeddings = embedding_model(chunks)

    # step 5: resolve document identity
    source_id = source_id or default_source_id(file_path)
    title = title or Path(file_path).name

    #step 6 store (replaces any earlier version of this source_id if exists)
    vectors = save_vector(chunks, embeddings, COLLECTION_NAME, source_id, title)

    print("Storing the file")
    return {
        "status": "ingested",
        "source_id": source_id,
        "title": title,
        "chunks": len(chunks),
    }