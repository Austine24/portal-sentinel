from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Portal Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],  # one exact origin, never "*"
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portal-sentinel-api"}
