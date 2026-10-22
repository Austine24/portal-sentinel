import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.api.routes.assessments import router as assessments_router
from app.api.routes.chain import router as chain_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.model import router as model_router
from app.api.routes.network import router as network_router
from app.portaldot.rpc import RpcError, RpcUnavailable
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("portal_sentinel")

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
app.include_router(model_router)
app.include_router(network_router)
app.include_router(chain_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "portal-sentinel-api"}


# Database failures become clean JSON errors. This matters for two reasons:
#  1. Unhandled exceptions produce a bare 500 WITHOUT CORS headers, so the browser reports a
#     misleading "cannot reach the API" instead of the real cause.
#  2. A raw error page can leak internals. Only a short, safe message leaves the server.
@app.exception_handler(OperationalError)
async def database_unavailable(request: Request, exc: OperationalError) -> JSONResponse:
    logger.error("database unavailable on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(status_code=503, content={"detail": "The database is unavailable. Is MySQL running?"})


@app.exception_handler(ProgrammingError)
async def database_not_ready(request: Request, exc: ProgrammingError) -> JSONResponse:
    logger.error("database schema problem on %s %s (%s)", request.method, request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "The database schema is not ready. Run: alembic upgrade head"},
    )


@app.exception_handler(RpcUnavailable)
async def node_unreachable(request: Request, exc: RpcUnavailable) -> JSONResponse:
    logger.error("portaldot node unavailable on %s %s (%s)", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={"detail": "The Portaldot node could not be reached, or it refused the request. Try again shortly."},
    )


@app.exception_handler(RpcError)
async def node_error(request: Request, exc: RpcError) -> JSONResponse:
    logger.error("portaldot node returned an error on %s %s (%s)", request.method, request.url.path, exc)
    return JSONResponse(status_code=502, content={"detail": "The Portaldot node returned an error."})
