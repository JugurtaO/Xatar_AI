import requests
from typing import List
import os

ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

class OllamaEmbedder:
    def __init__(self, base_url: str = ollama_url, model_name: str = "nomic-embed-text"):
        self.base_url = base_url
        self.model_name = model_name

    def embed(self, text: str) -> List[float]:
        # Ta méthode actuelle est parfaite pour une seule query
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model_name, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Envoie toute la liste au endpoint /api/embed d'Ollama (Vrai Batch)
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model_name,
                    "input": texts  # 'input' accepte une liste de strings
                },
                timeout=60
            )
            response.raise_for_status()
            # Le format de réponse pour /api/embed est {"embeddings": [[...], [...]]}
            return response.json()["embeddings"]
        except Exception as e:
            print(f"Erreur lors du batch embedding: {e}")
            # Fallback sur la méthode lente si l'endpoint échoue
            return [self.embed(t) for t in texts]
def get_embedding_model():
    return OllamaEmbedder()