from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/dummy")
def dummy():
    return {
        "status": "ok",
        "message": "FastAPI dummy response",
        "data": [1, 2, 3]
    }
