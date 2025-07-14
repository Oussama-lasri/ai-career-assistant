from pydantic import BaseModel , EmailStr , Field , SecretStr
from typing import Optional



class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    class Config:
        from_attributes = True
    
class UserInput(BaseModel):
    username: str | None
    email: str
    full_name: str | None = None
    password: SecretStr = Field(..., min_length=8, max_length=128)
    
class UserCreate(UserInput):
    pass

class userLogin(BaseModel):
    email: str
    password: SecretStr = Field(..., min_length=8, max_length=128)
    

class UserInDB(User):
    hashed_password: str