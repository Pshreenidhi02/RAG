#search in chroma db

from dataprocessing.chroma_store import get_client

def search_query(collection_name, question_embedding):
    client = get_client()

    collection = client.get_or_create_collection(name = collection_name)
    results = collection.query(query_embeddings=question_embedding.tolist(), n_results=2)
    print(results["documents"])
    
    return results
