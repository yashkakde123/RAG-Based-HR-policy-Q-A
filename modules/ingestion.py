import os
from fitz import open as open_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, docs_path="./data/documents"):
        self.docs_path = docs_path
        # REQ-02: 500-char chunks with 50-char overlap
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    def extract_and_chunk(self):
        """Reads PDFs and returns a list of dictionaries containing text and metadata."""
        all_chunks = []
        if not os.path.exists(self.docs_path) or len(os.listdir(self.docs_path)) == 0:
            return all_chunks

        for file_name in os.listdir(self.docs_path):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(self.docs_path, file_name)
                with open_pdf(file_path) as doc:
                    for page_num in range(len(doc)):
                        page_text = doc[page_num].get_text()
                        if not page_text.strip(): 
                            continue # Skip empty pages
                        
                        metadata = {"source": file_name, "page": page_num + 1}
                        chunks = self.splitter.split_text(page_text)
                        
                        for chunk in chunks:
                            all_chunks.append({"text": chunk, "metadata": metadata})
                            
        return all_chunks