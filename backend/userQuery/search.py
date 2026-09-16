#search in chroma db
import chromadb

def search_query(collection_name, question_embedding):
    client = chromadb.Client()

    collection = client.get_or_create_collection(name = collection_name)
    results = collection.query(query_embeddings=question_embedding.tolist(), n_results=2)
    print(results["documents"])
    
    return results
