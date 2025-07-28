import os
import uuid
from datetime import datetime
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from ..utils.document_processing_service import DocumentProcessingService
from ..models.Resume import Resume
from ..repositories.resume_repository import ResumeRepository


class ResumeService:

    UPLOAD_DIR = "uploads/resumes"

    def save_file(self ,user_id: int, file: UploadFile) -> str:
        allowed_extensions = ['.pdf', '.docx', '.html']
        extension = os.path.splitext(file.filename)[1].lower()

        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        user_folder = os.path.join(ResumeService.UPLOAD_DIR, str(user_id))
        os.makedirs(user_folder, exist_ok=True)

        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(user_folder, unique_filename)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        return file_path

    def process_resume(self, db: Session, file_path: str, user_id: int):
        print(f"\n=== PROCESSING RESUME ===")
        print(f"File path: {file_path}")
        print(f"User ID: {user_id}")
        
        # Step 1: Load document
        docs = DocumentProcessingService.load_document(file_path)
        print(f"Loaded documents: {len(docs)}")
        
        if docs:
            print(f"First document content length: {len(docs[0].page_content)}")
            print(f"First document content preview: {docs[0].page_content[:200]}...")
        else:
            print("ERROR: No documents loaded from file!")
            return None

        # Step 2: Add metadata
        metadata = {
            "user_id": user_id,
            "source": os.path.basename(file_path),
            "uploaded_at": datetime.now().isoformat()
        }
        docs = DocumentProcessingService.add_metadata(docs, metadata)
        print(f"Added metadata: {metadata}")

        # Create resume record in DB
        resume_repository = ResumeRepository(db)
        resume = Resume(
            user_id=user_id,
            filename=os.path.basename(file_path),
            upload_timestamp=datetime.utcnow()
        )
        resume_db = resume_repository.create_resume(resume)

        # Split documents
        chunks = DocumentProcessingService.split_documents(docs)
        print(f"Created chunks: {len(chunks)}")
        
        if chunks:
            print(f"First chunk content length: {len(chunks[0].page_content)}")
            print(f"First chunk metadata: {chunks[0].metadata}")
            print(f"First chunk content preview: {chunks[0].page_content[:200]}...")
        else:
            print("ERROR: No chunks created!")
            return None
        
        # Store in vector DB
        store_name = f"resume_{user_id}"
        DocumentProcessingService.store_documents(chunks, store_name)
        
        # Verify storage
        debug_info = DocumentProcessingService.debug_collection(store_name)
        print(f"Final verification: {debug_info}")

        return docs
    
    
    def ask_based_on_resume(self, user_id: int, question: str):
        """
        Ask a question based on the user's resume.
        """
        print(f"\n=== ASKING BASED ON RESUME ===")
        print(f"User ID: {user_id}")
        print(f"Question: {question}")

        # Get vector store for user's resume
        vector_store = DocumentProcessingService.get_vector_store(f"resume_{user_id}")
        
        if not vector_store:
            raise HTTPException(status_code=404, detail="Resume not found for this user.")
        
        # Retrieve relevant documents based on the user's question
        retrieved_docs = vector_store.similarity_search(question, k=5)
        
        if not retrieved_docs:
            return {
                "answer": "I don't have access to your resume information. Please upload your resume first.",
                "sources": []
            }
        
        print(f"Retrieved {len(retrieved_docs)} relevant documents")
        
        # Combine retrieved documents into context
        context = "\n\n".join([
            f"Resume Section {i+1}:\n{doc.page_content}" 
            for i, doc in enumerate(retrieved_docs)
        ])
        
        return {
            "question": question,
            "context": context,
            "relevant_documents": retrieved_docs
        }

        