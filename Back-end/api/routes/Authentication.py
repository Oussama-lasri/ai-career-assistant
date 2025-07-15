


from fastapi import APIRouter, Depends ,HTTPException 
from typing import Annotated
from ..services.authentication_service import authenticationService
from sqlalchemy.orm import Session
from ..core.database import DbSession
from ..schemas.User_schema import UserCreate 
from fastapi.security import OAuth2PasswordRequestForm
from ..schemas.Token_schema import Token


class AuthenticationRouter:
    def __init__(self):
        self.router = APIRouter(
            prefix="/authentication",
            tags=["Authentication"]
        )
        self.authentication_service = authenticationService()
        self.setup_routes()

    def setup_routes(self):
        @self.router.post("/login")
        async def login( db: DbSession  ,
                        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                        ) -> Token:
            self.authentication_service.authenticate_user(db,form_data.username, form_data.password)
            # Logic for user login
            return 

        @self.router.post("/register")
        async def register( db: DbSession ,user: UserCreate = Depends(UserCreate),):
            self.authentication_service.create_user(db,user)
            return {"message": "User registered successfully"}
        
        # Todos : /user/profile 
        #         /user/update-profile  
        #         /user/delete-profile 
    
# for export routers 
auth_router = AuthenticationRouter().router
        