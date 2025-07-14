from fastapi import FastAPI




app = FastAPI()

@app.get("/")
async def root():
    return("Hello from back-end!")




# if __name__ == "__main__":
#     main()
