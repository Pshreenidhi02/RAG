from dataprocessing.parser import parse_file
from dataprocessing.clean_text import clean_text
from dataprocessing.chunking import chunk_text
from dataprocessing.embedding import embedding_model
from dataprocessing.chroma_store import save_vector


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 250
COLLECTION_NAME = "my_selectiva_collection"

def process_file(file_path):
    print(f"Processing: {file_path}")
    
    # step 1
    text = parse_file(file_path)

    #step 2
    cleaned_text = clean_text(text)

    #step 3
    chunks = chunk_text(cleaned_text, max_chars=CHUNK_SIZE, overlap_chars=CHUNK_OVERLAP)

    #step 4
    embeddings = embedding_model(chunks)

    #step 5
    vectors = save_vector(chunks, embeddings, COLLECTION_NAME)

    print("Storing the file")
    return "Done"