import os
import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

class VectorDatabase:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        # Fixes M1: Swapped to BGE-Small and forced CPU device to save GPU VRAM
        # Changed from "cpu" to "cuda"
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"}
        )

    def save_chunks_to_db(self, chunks):
        """Initializes ChromaDB and saves the vectorized chunks."""
        if not chunks:
            return 0
        
        documents = [
            Document(page_content=c["text"], metadata=c["metadata"]) 
            for c in chunks
        ]
        
        vector_db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_model,
            persist_directory=self.db_path
        )
        return len(chunks)

    def retrieve_context_hybrid(self, query, top_k=3):
        """Fixes M3: Fuses Dense Vector Search and Lexical BM25 Search using a 
        custom, robust Reciprocal Rank Fusion (RRF) algorithm.
        """
        if not os.path.exists(self.db_path) or not os.listdir(self.db_path):
            return None, 0.0

        vector_db = Chroma(persist_directory=self.db_path, embedding_function=self.embedding_model)
        
        start_time = time.time()
        
        all_data = vector_db.get()
        if not all_data or not all_data['documents']:
            return None, 0.0
            
        langchain_docs = [
            Document(page_content=text, metadata=meta) 
            for text, meta in zip(all_data['documents'], all_data['metadatas'])
        ]
        
        bm25_retriever = BM25Retriever.from_documents(langchain_docs)
        bm25_retriever.k = top_k * 2 
        bm25_docs = bm25_retriever.invoke(query)
        
        vector_docs_with_scores = vector_db.similarity_search_with_score(query, k=top_k * 2)
        
        latency = time.time() - start_time
        
        # ==========================================
        # CUSTOM RECIPROCAL RANK FUSION (RRF)
        # ==========================================
        rrf_scores = {}
        doc_map = {}      
        scores_map = {}   
        
        for rank, (doc, score) in enumerate(vector_docs_with_scores, 1):
            content = doc.page_content
            doc_map[content] = doc
            scores_map[content] = score
            rrf_scores[content] = rrf_scores.get(content, 0) + 1.0 / (60 + rank)
            
        for rank, doc in enumerate(bm25_docs, 1):
            content = doc.page_content
            doc_map[content] = doc
            if content not in scores_map:
                scores_map[content] = 0.80
            rrf_scores[content] = rrf_scores.get(content, 0) + 1.0 / (60 + rank)
            
        sorted_contents = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
        
        fused_docs_with_scores = []
        for content in sorted_contents[:top_k]:
            fused_docs_with_scores.append((doc_map[content], scores_map[content]))
            
        return fused_docs_with_scores, latency
