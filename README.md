# Portal Sentinel

Security intelligence for the Portaldot ecosystem. Built for Portaldot Hacker House 2026, Track 3 (Node Operations & Tooling).

Monitor. Detect. Investigate. Verify.

> Status: early development. This page describes what exists today. **Network-health data is LIVE** from the Portaldot V3
> testnet. **Transaction data is DEMO / SIMULATED** (field `data_origin`) because the testnet currently carries almost no
> transactions; see `docs/PORTALDOT_VERIFIED_FACTS.md`.

## What exists so far
- Rule engine (transaction burst, value anomaly) with per-account baselines and explained evidence
- Isolation Forest anomaly model (ML-001) that compares each hour with the account's own normal and explains the shift (`docs/AI_MODEL.md`)
- Risk engine with configurable weights and risk bands
- Incident workflow (status transitions, audit timeline) stored in MySQL/MariaDB
- Evidence packages: frozen, canonical JSON per incident with a SHA-256 hash, plus a standalone verifier (`scripts/verify_evidence.py`, standard library only)
- React dashboard, incident list and detail pages talking to the API
- **Network health monitoring on live Portaldot testnet data** (block authors, finality lag, missed slots, stalled production) with a Network page; see `docs/NETWORK_HEALTH.md`
- Evidence registry contract with tests, and server-side verification of on-chain records (`docs/DEPLOYMENT.md` is the step-by-step deployment runbook)
- Read-only chain connectivity check script

Not done yet: the first real testnet deployment of the contract, live transaction ingestion, authentication.

## Run the backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
# optional: create backend\.env from ..\.env.example and set DATABASE_URL
alembic upgrade head
python -m pytest -q
uvicorn app.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

### MySQL / MariaDB setup (Laragon or XAMPP)
Start MySQL (Laragon: "Start All"), open a SQL console (Laragon: "Database" button, which opens HeidiSQL, then the Query tab) and run:
```sql
CREATE DATABASE portal_sentinel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sentinel'@'localhost' IDENTIFIED BY 'choose-a-password';
CREATE USER 'sentinel'@'127.0.0.1' IDENTIFIED BY 'choose-a-password';
GRANT ALL ON portal_sentinel.* TO 'sentinel'@'localhost';
GRANT ALL ON portal_sentinel.* TO 'sentinel'@'127.0.0.1';
```
Then set `DATABASE_URL=mysql+pymysql://sentinel:choose-a-password@127.0.0.1:3306/portal_sentinel?charset=utf8mb4` in `backend\.env`.
Use a password without special characters, or URL-encode them.

## Run the frontend
```powershell
cd frontend
npm install
npm run dev     # http://localhost:5173
npm run build   # type-check and build
```

## Architecture
![System architecture](docs/architecture.svg)

Full description: `docs/ARCHITECTURE.md`. The evidence flow diagram is `docs/evidence-flow.svg`.

## Documentation
- `docs/ARCHITECTURE.md` components, design decisions, security posture
- `docs/DEPLOYMENT.md` deployment runbook for the evidence registry
- `docs/CHECKIN_DRAFT.md` draft text for the hackathon check-in
- `docs/NETWORK_HEALTH.md` live network monitoring: signals, rules, limits
- `docs/AI_MODEL.md` how the anomaly model works and its limits
- `docs/DEMO_SCRIPT.md` the 3-minute demo script
- `docs/HACKATHON_SPEC.md` competition rules and dates
- `docs/PORTALDOT_VERIFIED_FACTS.md` what we have verified about Portaldot, and how
- `docs/PORTAL_SENTINEL_ROADMAP.md` plan and risks

## Third-party software
FastAPI, Uvicorn, Pydantic, pydantic-settings, SQLAlchemy, PyMySQL, cryptography, Alembic, scikit-learn with NumPy and SciPy (backend);
React, Vite, Tailwind CSS, React Router, Recharts, Framer Motion, Lucide, Zod (frontend).

## Verify an evidence hash yourself
On an incident page press "Prepare evidence package", then "Download JSON", then:
```powershell
python scripts\verify_evidence.py INC-00001-evidence.json 0xTHE_HASH_SHOWN_IN_THE_UI
```
It prints `MATCH` when the recomputed hash equals the one shown (or the one anchored on-chain later).

## License
MIT. See `LICENSE`. The contract file declares the same license in its SPDX header.

## Inspect the Portaldot testnet (read-only)
```powershell
python scripts\check_chain.py https://test-evm-rpc-v3.portaldot.dev 420420777
python scripts\inspect_chain.py
python scripts\probe_substrate.py --balance <your 5... address>
python scripts\evm_funding_address.py 0xYourDeployerAddress --check
python scripts\check_registry.py 0xDeployedContract
```
All send only read requests, with a descriptive User-Agent (the public RPC rejects Python's default one).
