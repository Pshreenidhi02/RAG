import chromadb


def save_vector(chunks, embeddings, collection_name):

    # Create ChromaDB client
    client = chromadb.Client()

    # Get existing collection or create a new one
    collection = client.get_or_create_collection(
        name=collection_name
    )

    # Create unique IDs
    ids = [
        f"chunk_{i}"
        for i in range(len(chunks))
    ]

    # Store/update vectors
    collection.upsert(
        documents=chunks,
        embeddings=embeddings.tolist(),
        ids=ids
    )

    print(
        f"Stored {len(chunks)} chunks in "
        f"'{collection_name}'"
    )

    return collection