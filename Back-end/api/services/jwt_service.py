from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, HTTPException , status
from ..schemas.Token_schema import Token , TokenData
from sqlalchemy.orm import Session
from ..repositories.user_repository import  UserRepository
from ..models.User import User
import jwt
from dotenv import load_dotenv
import os
load_dotenv()





class JwtService:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
        
    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> Token:
        to_encode = data.copy()
        print("Data to encode:", to_encode)
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return Token(access_token=encoded_jwt, token_type="bearer")
        # return encoded_jwt
        
    def decode_jwt(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=self.ALGORITHM)
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def get_current_user(self,db: Session,token):
            payload = self.decode_jwt(token)
            email = payload.get("sub")
            if email is None:
                raise HTTPException(status_code=401, detail="email not in payload")
            token_data = TokenData(email=email)
            user_repostory = UserRepository(db)
            user = user_repostory.get_user_by_email(email=token_data.email)
            if user is None:
                raise HTTPException(status_code=401, detail="Not Found the user with this email")
            return user
  
