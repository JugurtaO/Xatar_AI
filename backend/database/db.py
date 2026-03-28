import chromadb
from core.embeddings import get_embedding_model

_collection = None

def get_vector_db():
    global _collection
    if _collection is None:
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        _collection = client.get_or_create_collection(name="gen_ai_<rag")
        print("✅ Connexion à la collection établie")
    return _collection