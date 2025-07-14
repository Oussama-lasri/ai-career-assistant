from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import HTTPException 
from ..schemas.Token_schema import Token
import jwt
from dotenv import load_dotenv
import os
load_dotenv()





class JwtService:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM", "HS256")
        
    def create_access_token(self,data: dict, expires_delta: timedelta  | None = None) -> Token:
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
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
  
