from backend.core.embeddings.OllamaEmbedder import get_embedding_model
from backend.database.db import get_vector_db

def search_context(query_text, target_file_id=None, n_results=5):
    print("INSIDE SEARCH_CONTEXT")
    print(f"🔍 Recherche pour : '{query_text}' | Filtre PDF : {target_file_id}")
    collection = get_vector_db()
    embedder = get_embedding_model()
    print("AFTER EMBEDDER MODEL")
    query_vector = embedder.embed(query_text)
    
    search_params = {
        "query_embeddings": [query_vector],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }

    # Si un document spécifique est sélectionné, on filtre par métadonnée
    if target_file_id:
        search_params["where"] = {"source": target_file_id}

    results = collection.query(**search_params)
    
    # DEBUG : Combien de documents trouvés avant filtrage ?
    found_count = len(results['documents'][0]) if results['documents'] else 0
    print(f"📊 Documents trouvés par Chroma : {found_count}")

    # On transforme les résultats en un bloc de texte structuré
    relevant_chunks = []
    if results['documents'] and len(results['documents'][0]) > 0:
        for i in range(len(results['documents'][0])):
            # distance = results['distances'][0][i]
            # if distance > 0.8:  # Cosine distance — à calibrer selon tes données
            #     continue
            text = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            source = meta.get('source', 'Inconnu')
            page = meta.get('page', '?')
            
            relevant_chunks.append(f"[Extrait {i+1} | Source: {source}, Page: {page}]\n{text}")

    return "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else ""