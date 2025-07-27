from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, UnstructuredHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings ,ChatOpenAI
# from langchain_community.embeddings import HuggingFaceEmbeddings

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from typing import List
import os
from datetime import datetime
from dotenv import load_dotenv
import chromadb



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
        # for i, chunk in enumerate(chunks):
        #     chunk.metadata.update({"chunk_index": i, "chunk_size": len(chunk.page_content)})
        # print(f"Total chunks created: {len(chunks)}")
        # print(f"First chunk metadata: {chunks[0].documents if chunks else 'No chunks created'}")
        return chunks

    @classmethod
    def store_documents(cls,docs, store_name):  
        persistent_directory = os.path.join(cls.db_dir, store_name)
        if not docs:
            print("ERROR: No documents provided to store!")
            return
        try :
            if not os.path.exists(persistent_directory):
                print(f"\n--- Creating vector store {store_name} ---")
                db = Chroma.from_documents(
                    docs, cls.embeddings, 
                    persist_directory=persistent_directory,
                    collection_name=store_name
                )
                collection = db._collection
                verification = collection.get(include=['metadatas', 'documents'])
                print(f"Documents stored: {len(verification['documents'])}")
                print(f"--- Finished creating vector store {store_name} ---")
            else:
                print(
                    f"Vector store {store_name} already exists. No need to initialize.")
        except Exception as e:
            print(f"ERROR storing documents: {str(e)}")
            raise e
        
    
    # @classmethod
    # def create_vector_store(cls,docs, store_name):
    #     persistent_directory = os.path.join(cls.db_dir, store_name)
    #     if not os.path.exists(persistent_directory):
    #         print(f"\n--- Creating vector store {store_name} ---")
    #         db = Chroma.from_documents(
    #             docs, cls.embeddings, persist_directory=persistent_directory
    #         )
    #         print(f"--- Finished creating vector store {store_name} ---")
    #     else:
    #         print(
    #             f"Vector store {store_name} already exists. No need to initialize.")
            
    
    def get_strategy(strategy:str):
        if strategy == "recursive":
             return RecursiveCharacterTextSplitter
        #  add more strateges in future 
        else:
            raise ValueError(f"Unsupported splitting strategy: {strategy}")
        
    @classmethod
    def get_vector_store(cls, store_name: str):
        """Get a Chroma vector store for the specified collection."""
        persistent_directory =  os.path.join(cls.db_dir, store_name)
        print(f"Persistent directory: {persistent_directory}")
        # client = chromadb.PersistentClient(path=cls.db_dir)
        try:
            # collection = client.get_collection(name=store_name)
            return Chroma(
                # client=client,
                collection_name=store_name,
                embedding_function=cls.embeddings,
                persist_directory=persistent_directory
            )
        except Exception as e:
            raise ValueError(f"Collection {store_name} not found: {str(e)}")
    
    @classmethod
    def get_by_ids(cls, store_name: str, ids) -> dict:
        """Retrieve documents from the vector store by IDs."""
        vector_store = cls.get_vector_store(store_name)
        results = vector_store.get(ids=ids, include=["documents", "metadatas", "embeddings"])
        return results

    @classmethod
    def search_similar(cls, store_name: str, query_text: str, n_results: int = 5) -> dict:
        """Perform a similarity search on the vector store."""
        vector_store = cls.get_vector_store(store_name)
        results = vector_store.similarity_search_with_score(
            query=query_text,
            k=n_results
        )
        return {
            "documents": [doc.page_content for doc, score in results],
            "metadatas": [doc.metadata for doc, score in results],
            "scores": [score for doc, score in results]
        }

    @classmethod
    def search_by_metadata(cls, store_name: str, metadata_filter: dict, n_results: int = 5) -> dict:
        """Retrieve documents by metadata filter."""
        vector_store = cls.get_vector_store(store_name)
        results = vector_store.get(where=metadata_filter, include=["documents", "metadatas", "ids"])
        return results
    
    @classmethod
    def debug_collection(cls, store_name: str) -> dict:
        """Debug method to check collection contents."""
        try:
            vector_store = cls.get_vector_store(store_name)
            collection = vector_store._collection
            all_docs = collection.get(include=['metadatas', 'documents'])
            
            return {
                "collection_exists": True,
                "total_documents": len(all_docs['documents']),
                "sample_metadata": all_docs['metadatas'][:3] if all_docs['metadatas'] else [],
                "sample_document_preview": [doc[:100] + "..." if len(doc) > 100 else doc 
                                          for doc in all_docs['documents'][:2]],
                "document_ids": all_docs['ids'][:5] if all_docs['ids'] else []
            }
        except Exception as e:
            return {
                "collection_exists": False,
                "error": str(e)
            }