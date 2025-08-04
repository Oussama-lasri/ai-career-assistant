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
                print(f"Retrieved {len(relevant_docs)} relevant documents")


                if not relevant_docs:
                    return {
                        "status": "error",
                        "message": "No relevant resume documents found",
                        "user_id": user_id
                    }

                # 4. Construct RAG prompt
                context = "\n\n".join([doc.page_content for doc in relevant_docs])
                print(f"Context length: {context} characters")
                
                response = self.RAGService.ask_model_with_question(context = context , question = question) 
                # print(f"Model response: {response.content}")

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

        @self.router.get("/rate")
        def rate_resume(
            token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
            db: DbSession,
        ):
            """
            Rate the user's resume using AI based on all available resume content.
            """
            
            try:
                # 1. Authenticate user
                print(f"\n=== RATING RESUME ===")
                jwt_service = JwtService()
                user = jwt_service.get_current_user(db , token)
                user_id = user.id

                # 2. Load the vector store
                vector_store = DocumentProcessingService.get_vector_store(f"resume_{user_id}")

                # 3. Retrieve relevant documents (whole resume or top-k)
                resume_docs = vector_store.similarity_search("Rate this resume", k=15)
                if not resume_docs:
                    raise HTTPException(status_code=404, detail="No resume content found for rating")

                # 4. Combine context from documents
                context = "\n\n".join([doc.page_content for doc in resume_docs])
                print(f"Resume context length: {len(context)} characters")

                # 5. Ask model using RAGService
                response = self.RAGService.ask_model(context=context, service_type="rate_resume")

                return {
                    "status": "success",
                    "user_id": user_id,
                    "service": "rate_resume",
                    "answer": response.content if hasattr(response, "content") else response,
                }

            except HTTPException as http_err:
                raise http_err

            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to rate resume: {str(e)}"
                }
                
        @self.router.get("/service/{service_type}/pipeline")
        def resume_service_pipeline(
                service_type: str,
                token: Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="authentication/login"))],
                db: DbSession,
                question: str = None
            ):
                """
                Use the complete RAG pipeline from RAGService (alternative approach)
                """
                
                
                # Validate service type
                valid_services = ["answer_question", "rate_resume", "suggest_improvements", "analyze_skills"]
                if service_type not in valid_services:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid service type. Valid options: {', '.join(valid_services)}"
                    )
                
                
                if service_type == "answer_question" and not question:
                    raise HTTPException(
                        status_code=400,
                        detail="Question parameter is required for 'answer_question' service"
                    )
                
                try:
                    # Authenticate
                    jwt_service = JwtService()
                    user = jwt_service.get_current_user(db, token)
                    user_id = user.id
                    
                    print(f"\n=== PIPELINE SERVICE: {service_type.upper()} ===")
                    print(f"User ID: {user_id}")

                    # Use RAGService complete pipeline
                    if service_type == "answer_question":
                        response = self.RAGService.get_response(
                            question=question,
                            service_type=service_type
                        )
                    else:
                        # For non-question services, use a generic query
                        generic_query = f"Analyze resume for {service_type}"
                        print(f"Using generic query: {generic_query}")
                        response = self.RAGService.get_response(
                            question=f"Analyze resume for {service_type}",
                            service_type=service_type,
                            k=15
                        )
                        return response

                    return {
                        "status": "success",
                        "user_id": user_id,
                        "service_type": service_type,
                        "question": question if question else None,
                        "answer": response.content if hasattr(response, "content") else str(response),
                        "method": "pipeline"
                    }

                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Vector store not found: {str(e)}",
                        "suggestion": "Upload a resume first",
                        "service_type": service_type
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"Failed to process {service_type}: {str(e)}",
                        "service_type": service_type
                    }

            
resume_router = resumeRouter().router


