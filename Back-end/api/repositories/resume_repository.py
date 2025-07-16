from ..models.Resume import Resume
from ..models.User import User
from sqlalchemy.orm import Session

class ResumeRepository:
    def __init__(self, db: Session):
        self.db = db
    def create_resume(self, resume: Resume) -> Resume:
        db_resume = resume
        self.db.add(db_resume)
        self.db.commit()
        self.db.refresh(db_resume)
        return db_resume

    def get_resume_by_id(self, resume_id: int) -> Resume | None:
        return self.db.query(Resume).filter(Resume.id == resume_id).first()
    
    def get_all_resumes(self):
        return self.db.query(Resume).all()
    
    def get_resumes_by_user_id(self, user_id: int) -> list[Resume]:
        return self.db.query(Resume).filter(Resume.user_id == user_id).all()
    
    def delete_resume(self, resume_id: int) -> None:
        resume = self.get_resume_by_id(resume_id)
        if resume:
            self.db.delete(resume)
            self.db.commit()
        else:
            raise ValueError("Resume not found")
        
        
    def update_resume(self, resume_id: int, updated_data: dict) -> Resume:
        resume = self.get_resume_by_id(resume_id)
        if not resume:
            raise ValueError("Resume not found")
        
        for key, value in updated_data.items():
            setattr(resume, key, value)
        
        self.db.commit()
        self.db.refresh(resume)
        return resume