import os
import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

class VectorDatabase:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        # REQ-02: Embeddings via all-MiniLM-L6-v2
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    def save_chunks_to_db(self, chunks):
        """Converts chunks to vectors and persists to local SQLite database."""
        if not chunks:
            return 0
        
        vector_db = Chroma.from_texts(
            texts=[c["text"] for c in chunks],
            embedding=self.embedding_model,
            metadatas=[c["metadata"] for c in chunks],
            persist_directory=self.db_path
        )
        return len(chunks)

    def retrieve_context(self, query, top_k=3):
        """Retrieves matching chunks and returns latency."""
        if not os.path.exists(self.db_path) or not os.listdir(self.db_path):
            return None, 0.0

        vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embedding_model)
        
        start_time = time.time()
        # REQ-03: Cosine similarity against Top-K
        retrieved_docs_with_scores = vector_db.similarity_search_with_score(query, k=top_k)
        latency = time.time() - start_time
        
        return retrieved_docs_with_scores, latency