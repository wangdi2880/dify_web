import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the 'api' directory is in the path for Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from routes.dify_routes import router as dify_router

app = FastAPI()
# Reload trigger
app.include_router(dify_router)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def read_root():
    return {"message": "Hello from Dockerized FastAPI!"}
