from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from ..services.resume_service import ResumeService
from ..services.jwt_service import JwtService
from ..core.database import DbSession
import os

class resumeRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/resume", tags=["Resume"])
        self.resumeService = ResumeService()
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

resume_router = resumeRouter().router
