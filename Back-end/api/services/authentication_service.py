

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends , HTTPException, status
from sqlalchemy.orm import Session
from ..repositories.user_repository import UserRepository
from ..schemas.User_schema import UserCreate , UserInDB , User as UserSchema
from ..models.User import User


class authenticationService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/login")
    
    
    def authenticate_user(self, db: Session, email: str, password: str) -> UserInDB | None:
        user = self.get_user(db,email)
        if not user :
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
        
        

    def create_user(self, db: Session, user: UserCreate):
        new_user = User(**user.model_dump(exclude={"password"}))
        new_user.hashed_password = self.get_password_hash(user.password.get_secret_value())

        if self.get_user(db,user.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user_repository = UserRepository(db)
        created_user = user_repository.create_user(new_user)

        # Conversion ORM → Pydantic
        return UserSchema.model_validate(created_user)

    def get_password_hash(self,password):
        return self.pwd_context.hash(password)
    
    def get_user(self,db: Session ,email: str ):
        user_repository = UserRepository(db)
        user_dict = user_repository.get_user_by_email(email)
        if user_dict is None:
            return None 

        return UserInDB.model_validate(user_dict)
    
    def verify_password(self,plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)