import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.embeddings.OllamaEmbedder import get_embedding_model
from backend.database.db import get_vector_db #singleton

def process_pdf_with_status(file_path):
    try:
        file_name = os.path.basename(file_path)
        
        # 1. EXTRACTION
        yield "extracting:10"
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        yield "extracting:30"

        # 2. CHUNKING
        yield "chunking:40"
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=70
        )
        chunks = text_splitter.split_documents(pages)
        yield "chunking:60"

        # 3. EMBEDDING & STORAGE
        yield "embedding:70"
        collection = get_vector_db()
        embed_model = get_embedding_model() 

        for i, chunk in enumerate(chunks):
            # Générer le vecteur via Ollama
            vector = embed_model.embed_query(chunk.page_content)
            
            # Stocker dans Chroma avec les métadonnées pour le filtrage
            collection.add(
                ids=[f"{file_name}_{i}"],
                embeddings=[vector],
                documents=[chunk.page_content],
                metadatas=[{"source": file_name, "page": chunk.metadata.get("page", 0) + 1}]
            )
            
            # Mise à jour de la barre de progression dynamiquement
            if i % 5 == 0:
                progress = 70 + int((i / len(chunks)) * 25)
                yield f"embedding:{progress}"

        yield "done:100"

    except Exception as e:
        print(f"Erreur ingestion: {e}")
        yield f"error:{str(e)}"