from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage 
from typing import Annotated
from ..services.resume_service import ResumeService
from ..services.rag_service import RAGService
from ..services.jwt_service import JwtService
from ..core.database import DbSession
import os
from ..utils.document_processing_service import DocumentProcessingService
from pprint import pprint

from dotenv import load_dotenv
load_dotenv()


class resumeRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/resume", tags=["Resume"])
        self.resumeService = ResumeService()
        self.RAGService = RAGService()
        self.setup_routes()

    def setup_routes(self):

        @self.router.post("/upload", status_code=status.HTTP_201_CREATED)
        def upload_resume(
            token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
            db: DbSession,
            file: UploadFile = File(...)
        ):
            allowed_extensions = ['.pdf', '.docx', '.html']
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file type. Only PDF, DOCX, and HTML files are allowed."
                )

            jwt_service = JwtService()
            user = jwt_service.get_current_user(db, token)
            user_id = user.id

            # Save file
            file_path = self.resumeService.save_file(user_id, file)

            try:
                # Process the resume (load document, add metadata, save in DB )
                self.resumeService.process_resume(db, file_path, user_id)

            finally:
                # remoce the temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)

            return {"message": f"Resume uploaded successfully, file name: {file.filename}"}

        
    #     @self.router.get("/ask")
    #     def ask(
    #         token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
    #         db: DbSession,
    #     ):
    # #         Guidelines:
    # # - Only answer based on the information provided in the resume context
    # # - If the information is not available in the resume, clearly state that
    # # - Be specific and cite relevant details from the resume
    # # - Maintain a professional and helpful tone
    #         contextualize_q_system_prompt= """            
    #         You are a helpful AI assistant that provides information based on the user's resume.
    #         The user has uploaded their resume, and you can answer questions about it.
    #         Use the information from the resume to provide accurate and relevant answers. 
    #         """
            
    #         jwt_service = JwtService()
    #         user = jwt_service.get_current_user(db, token)
    #         user_id = user.id
        
    #         vector_store = DocumentProcessingService.get_vector_store(f"resume_{str(user_id)}")
            
    #         retrieve_query = "What is the user's name?"
    #         print(f"Retrieving documents for query: {retrieve_query}")
    #         retrieved_docs = vector_store.similarity_search(retrieve_query, k=20)
    #         print(f"Retrieved {len(retrieved_docs)} documents.")
    #         if not retrieved_docs:
    #             raise HTTPException(status_code=404, detail="No documents found for the query.")
    #         print(f"First retrieved document content: {retrieved_docs[0].page_content[:200]}...")
    #         print(f"First retrieved document metadata: {retrieved_docs[0].metadata}")
    #         return {
    #             "retrieved_documents": [
    #                 {"content": doc.page_content, "metadata": doc.metadata} for doc in retrieved_docs
    #             ]
    #         }
            
        
    #     @self.router.get("/debug/{user_id}")
    #     def debug_collection(user_id: int):
    #         store_name = f"resume_{user_id}"
    #         debug_info = DocumentProcessingService.debug_collection(store_name)
    #         return {
    #             "collection_name": store_name,
    #             "debug": debug_info
    #         }
        @self.router.get("/ask2")
        def ask(
            token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
            db: DbSession,
            question: str = "What is the user's name?",  # Default question for testing
            
        ):
            model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                client_options=None,
                transport=None,
                additional_headers=None,
                client=None,
                async_client=None
            )
            system_prompt = """
                You are a helpful AI assistant that provides information based on the user's resume.
                You have access to the user's resume content through the provided context documents.
                
                Instructions:
                - Answer questions accurately based ONLY on the information in the resume
                - If the information is not in the resume, clearly state that
                - Be conversational and helpful
                - Provide specific details when available (dates, company names, skills, etc.)
                - If asked about experience, mention relevant projects, jobs, or education
                """
            
            

            
            try:
                # Get current user
                jwt_service = JwtService()
                user = jwt_service.get_current_user(db, token)
                user_id = user.id
                
                # Get vector store
                vector_store = DocumentProcessingService.get_vector_store(f"resume_{str(user_id)}")
                
                print(f"Testing with question: {question}")
                print(f"User ID: {user_id}")
                
                system_message = SystemMessage(content=system_prompt)
                user_prompt = HumanMessage(content=question)
                messages = [system_message, user_prompt]
                
                response = model.invoke(messages)
                
                # Retrieve relevant documents
                retrieved_docs = vector_store.similarity_search(question, k=3)
                
                if not retrieved_docs:
                    return {
                        "status": "error",
                        "message": "No documents found",
                        "question": question,
                        "user_id": user_id
                    }
                
                print(f"Found {len(retrieved_docs)} documents")
                
                # Simple response - just return the relevant content
                return {
                    "status": "success",
                    "question": question,
                    "user_id": user_id,
                    "total_documents_found": len(retrieved_docs),
                    # "relevant_content": [
                    #     {
                    #         "content": doc.page_content,
                    #         "metadata": {
                    #             "source": doc.metadata.get("source", "unknown"),
                    #             "user_id": doc.metadata.get("user_id", "unknown")
                    #         }
                    #     }
                    #     for doc in retrieved_docs
                    # ]
                }
                
            except ValueError as e:
                return {
                    "status": "error",
                    "message": f"Collection not found: {str(e)}",
                    "suggestion": "Upload a resume first"
                }
                
            except Exception as e:
                return {
                    "status": "error", 
                    "message": f"Error: {str(e)}",
                    "question": question
                }
                
        @self.router.get("/ask")
        def ask_resume(
            token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
            db: DbSession,
            question: str   # Default question for testing
            
        ):
            # 1. Auth
            # 2. Load vector store
            # 3. Search similar docs
            # 4. Prompt construction
            # 5. Call model
            """
            RAG-based endpoint: Ask questions about the user's resume
            """
            try:
                # 1. Authenticate
                jwt_service = JwtService()
                user = jwt_service.get_current_user(db, token)
                user_id = user.id

                # 2. Load user's vector DB
                vector_store = DocumentProcessingService.get_vector_store(f"resume_{user_id}")

                # 3. Retrieve relevant resume chunks
                relevant_docs = vector_store.similarity_search(question, k=3)

                if not relevant_docs:
                    return {
                        "status": "error",
                        "message": "No relevant resume documents found",
                        "user_id": user_id
                    }

                # 4. Construct RAG prompt
                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                response = self.RAGService.ask_model(context, question) 
                print(f"Model response: {response.content}")

                return {
                    "status": "success",
                    "user_id": user_id,
                    "question": question,
                    "answer": response.content,
                }

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to answer question: {str(e)}"
                }
resume_router = resumeRouter().router


