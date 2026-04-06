import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.core.embeddings.OllamaEmbedder import get_embedding_model
from backend.database.db import get_vector_db
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
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(pages)
        yield "chunking:60"

        # 3. EMBEDDING & STORAGE
        yield "embedding:70"
        collection = get_vector_db()
        embed_model = get_embedding_model() 

        batch_size = 25 # Taille du lot
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            batch_texts = [c.page_content for c in batch]
            batch_ids = [f"{file_name}_{idx}" for idx in range(i, i + len(batch))]
            batch_metadatas = [{"source": file_name, "page": c.metadata.get("page", 0) + 1} for c in batch]

            # 1. UN SEUL APPEL API pour tous les vecteurs du lot
            batch_vectors = embed_model.embed_documents(batch_texts)

            print("###########>", batch_metadatas[0])
            # 2. UN SEUL APPEL API pour stocker dans ChromaDB
            collection.add(
                ids=batch_ids,
                embeddings=batch_vectors,
                documents=batch_texts,
                metadatas=batch_metadatas
            )

            progress = 50 + int((i / len(chunks)) * 45)
            yield f"embedding:{progress}"

        yield "done:100"
    except Exception as e:
        yield f"error:{str(e)}"