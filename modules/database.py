import os
import time
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

class VectorDatabase:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        
        # DECLARE IMMEDIATELY: Prevents attribute errors during startup
        self.vector_db = None
        self.bm25_retriever = None
        
        # REQ-02: Initializing the bge-base-en-v1.5 model (768 dimensions)
        self.embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
        self._load_db()

    def _load_db(self):
        """Loads database connections and caches both Chroma and BM25 search indexes in memory."""
        if os.path.exists(self.db_path) and os.listdir(self.db_path):
            self.vector_db = Chroma(
                persist_directory=self.db_path, 
                embedding_function=self.embedding_model
            )
            
            # Extract stored documents to construct and cache the BM25 index
            stored_data = self.vector_db.get()
            if stored_data and stored_data.get("documents"):
                doc_list = []
                for text, meta in zip(stored_data["documents"], stored_data["metadatas"]):
                    doc_list.append(Document(page_content=text, metadata=meta))
                
                # Cache the BM25 retriever instance
                self.bm25_retriever = BM25Retriever.from_documents(doc_list)
            else:
                self.bm25_retriever = None
        else:
            self.vector_db = None
            self.bm25_retriever = None

    def save_chunks_to_db(self, chunks):
        """Appends new chunks to the database and automatically updates the cached indexes."""
        if not chunks:
            return 0
        
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        if self.vector_db is None:
            self.vector_db = Chroma.from_texts(
                texts=texts,
                embedding=self.embedding_model,
                metadatas=metadatas,
                persist_directory=self.db_path
            )
        else:
            self.vector_db.add_texts(texts=texts, metadatas=metadatas)
        
        # Refresh the cached database and BM25 index on the fly
        self._load_db()
        return len(chunks)

    def retrieve_context_hybrid(self, query, top_k=3):
        """Retrieves matching chunks utilizing a manual Reciprocal Rank Fusion (BM25 + Semantic).
        OPTIMIZED: Uses In-Memory caching to achieve < 5s latency.
        """
        # 1. Use the CACHED databases (Bypasses disk I/O for instant retrieval)
        if self.vector_db is None:
            self._load_db()
            if self.vector_db is None:
                return [], 0.0, 9.9

        start_time = time.time()
        
        # 2. Fetch from cached Vector Database
        vector_docs_with_scores = self.vector_db.similarity_search_with_score(query, k=top_k * 2)
        
        # Capture absolute best distance for the security guardrail in app.py
        absolute_best_distance = vector_docs_with_scores[0][1] if vector_docs_with_scores else 9.9
        
        # 3. Fetch from cached BM25 Database
        bm25_docs = []
        if self.bm25_retriever is not None:
            self.bm25_retriever.k = top_k * 2
            bm25_docs = self.bm25_retriever.invoke(query)
            
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
            scores_map[content] = score  # Preserves your real Chroma score!
            rrf_scores[content] = rrf_scores.get(content, 0) + 1.0 / (60 + rank)
            
        for rank, doc in enumerate(bm25_docs, 1):
            content = doc.page_content
            doc_map[content] = doc
            if content not in scores_map:
                scores_map[content] = 0.80  # Fallback for keyword-only matches
            rrf_scores[content] = rrf_scores.get(content, 0) + 1.0 / (60 + rank)
            
        sorted_contents = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
        
        fused_docs_with_scores = []
        for content in sorted_contents[:top_k]:
            fused_docs_with_scores.append((doc_map[content], scores_map[content]))
            
        # Returns 3 variables to match our updated app.py logic
        return fused_docs_with_scores, latency, absolute_best_distance
