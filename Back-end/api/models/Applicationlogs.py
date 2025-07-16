from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..core.database import Base


class ApplicationLog(Base):
    __tablename__ = 'application_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user_input = Column(String, nullable=False)  
    model_response = Column(String, nullable=False)  
    feedback = Column(String, nullable=True)  
    timestamp = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="application_logs") 