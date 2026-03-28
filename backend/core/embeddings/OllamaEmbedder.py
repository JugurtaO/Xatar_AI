from langchain_ollama import OllamaEmbeddings
import os

# On utilise un cache simple pour éviter de réinitialiser le modèle à chaque appel
_model = None

def get_embedding_model():
    """
    Initialise et retourne le modèle d'embedding configuré dans Ollama.
    """
    global _model
    if _model is None:
        # Si tu tournes dans Docker, l'URL doit pointer vers le nom du service 'ollama'
        # Sinon, 'localhost' par défaut.
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # nomic-embed-text est le standard actuel (performant et léger)
        # Assure-toi d'avoir fait un `ollama pull nomic-embed-text`
        _model = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url=ollama_base_url
        )
        print(f"✅ Modèle d'embedding prêt (via {ollama_base_url})")
        
    return _model