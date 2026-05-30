from dotenv import load_dotenv
load_dotenv()  # Must be first, before any other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.services.chat_engine import chat

app = FastAPI(title="ChatOps AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def root():
    return {"status": "ChatOps AI Backend running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        reply = chat(req.message, req.history)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "exhausted" in error_msg.lower() or "rate_limit" in error_msg.lower():
            reply = "⚠️ API rate limit reached. Please wait a minute and try again."
        elif "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            reply = "⚠️ API key error. Please check your GROQ_API_KEY in the .env file."
        else:
            reply = f"⚠️ An error occurred: {error_msg}"
    return ChatResponse(reply=reply)