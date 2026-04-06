import chromadb
import os

_collection = None

def get_vector_db():
    global _collection
    if _collection is None:
        host = os.getenv("CHROMA_HOST", "localhost") 
        
        client = chromadb.HttpClient(host=host, port=8000)
        
        # On définit la méthode de calcul de distance (HNSW) pour la précision
        _collection = client.get_or_create_collection(
            name="xatar_rag_collection",
            metadata={"hnsw:space": "cosine"} # Cosine similarity est idéal pour le RAG
        )
        print(f"✅ Connexion à ChromaDB ({host}) établie")
    return _collection