from dataprocessing.embedding import embedding_model
from userQuery.search import search_query
from userQuery.send_to_LLM import send_to_LLM

COLLECTION_NAME = "my_selectiva_collection"

def ask(query):
    print(f"userQuestion is this: {query}")


    
    #step 1: Query embedding
    embeddings = embedding_model([query])

    #step 2: search the query embedding in vector db through semantic search
    relevant_context = search_query(COLLECTION_NAME, embeddings)

    #step 3: sending the most relevant chunks to LLM OpenAI
    Answer = send_to_LLM(query, relevant_context)

    return Answer