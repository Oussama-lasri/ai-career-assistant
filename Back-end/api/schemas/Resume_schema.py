from pydantic import BaseModel
from datetime import datetime

class ResumeBase(BaseModel):
    
    filename: str

class ResumeCreate(ResumeBase):
    pass  

class ResumeOut(ResumeBase):
    id: int
    user_id: int
    upload_timestamp: datetime

    class Config:
        orm_mode = True