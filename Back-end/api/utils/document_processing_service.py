from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
import os
from datetime import datetime

class DocumentProcessingService:

    @staticmethod
    def load_document(file_path: str) -> List[Document]:
        if file_path.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith('.docx'):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith('.html'):
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
        return loader.load()

    @staticmethod
    def add_metadata(documents: List[Document], metadata: dict) -> List[Document]:
        for doc in documents:
            doc.metadata.update(metadata)
        return documents

    @staticmethod
    def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 100, strategy: str = "recursive") -> List[Document]:
        if strategy == "recursive":
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        else:
            raise ValueError(f"Unsupported splitting strategy: {strategy}")
        
        chunks = splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({"chunk_index": i, "chunk_size": len(chunk.page_content)})
        return chunks

    @staticmethod
    def index_document_to_chroma() :
        # return true or false
        pass
    
    