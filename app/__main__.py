"""CLI runner for python -m app."""
import os
import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    port = int(os.getenv("PORT", PORT))
    print(f"Starting Ask-the-Numbers on http://{HOST}:{port} ...")
    uvicorn.run("app.main:app", host=HOST, port=port, reload=True)
