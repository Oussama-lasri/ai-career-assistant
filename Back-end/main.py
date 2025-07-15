from fastapi import FastAPI
from api.utils.init_db import create_tables
from api.routes.Authentication  import auth_router
from api.core.middlewares import AuthMiddleware




app = FastAPI()
app.add_middleware(AuthMiddleware)

# Initialize the database and create tables
# create_tables()

app.include_router(auth_router)


@app.get("/")
async def root():
    return("Hello from back-end!")




# if __name__ == "__main__":
#     main()
