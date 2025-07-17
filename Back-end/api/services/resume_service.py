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

    def save_file(user_id: int, file: UploadFile) -> str:
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

    def process_resume(db: Session, file_path: str, user_id: int):
        # Step 1: Load document
        docs = DocumentProcessingService.load_document(file_path)

        # Step 2: Add metadata
        metadata = {
            "user_id": user_id,
            "source": os.path.basename(file_path),
            "uploaded_at": datetime.utcnow().isoformat()
        }
        docs = DocumentProcessingService.add_metadata(docs, metadata)

        # Create resume record in DB
        resume_repository = ResumeRepository(db)
        resume = Resume(
            user_id=user_id,
            filename=os.path.basename(file_path),
            upload_timestamp=datetime.utcnow()
        )
        resume_repository.create_resume(resume)

        # Optionally split and store in vector DB
        # chunks = DocumentProcessingService.split_documents(docs)
        # RAGService().store_documents(chunks)
        # return chunks

        return docs  # ou return resume si tu préfères
