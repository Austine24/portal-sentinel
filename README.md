# Portal Sentinel

Security intelligence for the Portaldot ecosystem. Built for Portaldot Hacker House 2026, Track 3 (Node Operations & Tooling).

Monitor. Detect. Investigate. Verify.

> Status: early development. Everything on this page describes what exists today; see `docs/` for the plan.

## What exists so far
- Backend skeleton (FastAPI) with a health endpoint
- A read-only chain connectivity check script

## Run the backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/health

## Documentation
- `docs/HACKATHON_SPEC.md` competition rules and dates
- `docs/PORTALDOT_VERIFIED_FACTS.md` what we have verified about Portaldot, and how
- `docs/PORTAL_SENTINEL_ROADMAP.md` plan and risks

## Third-party software
FastAPI, Uvicorn, Pydantic, pydantic-settings (see `backend/requirements.txt`).
