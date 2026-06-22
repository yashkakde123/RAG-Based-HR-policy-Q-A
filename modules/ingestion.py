import os
import re
from fitz import open as open_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, docs_path="./data/documents"):
        self.docs_path = docs_path
        # Fixes Chunking Mismatch: Updated to SRS v4.0 parameters
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)

    def clean_pii(self, text):
        """M-10/REQ-10: Redacts sensitive PII from text before embedding generation."""
        text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
        text = re.sub(r'\b(?:\+91|0)?[6-9]\d{9}\b', '[REDACTED_PHONE]', text)
        text = re.sub(r'\b\d{4}[\s-]\d{4}[\s-]\d{4}\b', '[REDACTED_AADHAAR]', text)
        text = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]{1}\b', '[REDACTED_PAN]', text)
        return text

    def extract_and_chunk(self):
        """Reads PDFs, cleans PII, and returns chunk dictionaries."""
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
                            continue
                        
                        cleaned_text = self.clean_pii(page_text)
                        
                        metadata = {"source": file_name, "page": page_num + 1}
                        chunks = self.splitter.split_text(cleaned_text)
                        
                        for chunk in chunks:
                            all_chunks.append({"text": chunk, "metadata": metadata})
                            
        return all_chunks
