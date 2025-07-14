from ..core.database import Base, engine
from ..models.User import User


def create_tables():
    """
    Initialize the database by creating all tables.
    This function should be called at the start of the application.
    """
    User.metadata.create_all(bind=engine)
  
    
   
    Base.metadata.create_all(bind=engine)
    print("Database initialized and tables created.")