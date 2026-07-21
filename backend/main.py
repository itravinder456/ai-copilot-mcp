from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat_router import chat_router
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = FastAPI(
    title="AI Copilot API",
    description="An API for AI Copilot functionalities, providing endpoints for various AI-driven features and services.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["Chat"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
