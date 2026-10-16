from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.assessments import router as assessments_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.incidents import router as incidents_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Portal Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],  # one exact origin, never "*"
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


app.include_router(assessments_router)
app.include_router(incidents_router)
app.include_router(evidence_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portal-sentinel-api"}
