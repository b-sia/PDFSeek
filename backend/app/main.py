from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import pdf, chat, model

app = FastAPI(
    title="PDF Chat API",
    description="API for chatting with PDF documents using various LLM models",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pdf.router, prefix="/api/pdf", tags=["pdf"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(model.router, prefix="/api/model", tags=["model"])

@app.get("/")
async def root():
    return {"message": "Welcome to PDF Chat API"}
