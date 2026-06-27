"""Convenience launcher: `python run.py` starts the UrbanCool AI backend."""

import uvicorn

from app.config import settings

if __name__ == "__main__":
    reload = settings.ENVIRONMENT == "development"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
    )
