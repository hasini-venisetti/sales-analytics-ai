"""FastAPI application entry point serving API and static frontend UI."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import HOST, PORT
from app.api.routes import router as api_router
from app.data.etl import run_etl

app = FastAPI(
    title="Ask-the-Numbers: Trustworthy Mini AI Business Intelligence Assistant",
    description="Natural language questions over sales data with verified queries, dual-engine validation, and audit proof panels.",
    version="1.0.0"
)

# Enable CORS for local dev and preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Static files setup
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def startup_event():
    """Ensure database and data quality reports are bootstrapped."""
    run_etl()


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the single-page application frontend directly from FastAPI."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Ask-the-Numbers API is running. UI index.html not yet placed in static directory."}


if __name__ == "__main__":
    import uvicorn
    # Use PORT from env var (supports custom port or default 8000)
    port = int(os.getenv("PORT", PORT))
    uvicorn.run("app.main:app", host=HOST, port=port, reload=True)
