from fastapi import FastAPI
from api.utils.init_db import create_tables




app = FastAPI()

# Initialize the database and create tables
# create_tables()


@app.get("/")
async def root():
    return("Hello from back-end!")




# if __name__ == "__main__":
#     main()
