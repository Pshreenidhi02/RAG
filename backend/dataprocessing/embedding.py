from sentence_transformers import SentenceTransformer

def embedding_model(chunks,model_name= "all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)

    ###Generate embeddings:
    embeddings = model.encode(chunks)

    print(embeddings.shape)

    return embeddings

