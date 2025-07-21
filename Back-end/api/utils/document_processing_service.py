from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings ,ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List
import os
from datetime import datetime
from dotenv import load_dotenv



class DocumentProcessingService:
    load_dotenv()
    # embeddings = OpenAIEmbeddings()  
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") 
    db_dir = "chroma_db"
        

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
        splitter = DocumentProcessingService.get_strategy(strategy)(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        chunks = splitter.split_documents(documents)
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({"chunk_index": i, "chunk_size": len(chunk.page_content)})
        return chunks

    @classmethod
    def store_documents(cls,docs, store_name):  
        persistent_directory = os.path.join(cls.db_dir, store_name)
        if not os.path.exists(persistent_directory):
            print(f"\n--- Creating vector store {store_name} ---")
            db = Chroma.from_documents(
                docs, cls.embeddings, persist_directory=persistent_directory
            )
            print(f"--- Finished creating vector store {store_name} ---")
        else:
            print(
                f"Vector store {store_name} already exists. No need to initialize.")
        pass
    
    @classmethod
    def create_vector_store(cls,docs, store_name):
        persistent_directory = os.path.join(cls.db_dir, store_name)
        if not os.path.exists(persistent_directory):
            print(f"\n--- Creating vector store {store_name} ---")
            db = Chroma.from_documents(
                docs, cls.embeddings, persist_directory=persistent_directory
            )
            print(f"--- Finished creating vector store {store_name} ---")
        else:
            print(
                f"Vector store {store_name} already exists. No need to initialize.")
            
    
    def get_strategy(strategy:str):
        if strategy == "recursive":
             return RecursiveCharacterTextSplitter
        #  add more strateges in future 
        else:
            raise ValueError(f"Unsupported splitting strategy: {strategy}")