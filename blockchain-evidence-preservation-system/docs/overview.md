# Blockchain Evidence Preservation System (BEPS)

## Overview

BEPS is a tamper-proof digital evidence management system designed for law enforcement agencies, forensic investigators, and legal proceedings. It combines a **FastAPI** backend, a **Vue.js** frontend, **PostgreSQL** for relational data, and **Ethereum smart contracts** for immutable evidence registration and chain-of-custody tracking.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Vue.js Frontend                   │
│          (Evidence Upload, Case Management,          │
│           Chain of Custody Viewer)                   │
└────────────────────┬────────────────────────────────┘
                     │ REST API (JWT-secured)
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│    ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│    │  Routes  │  │ Services │  │   Use Cases    │   │
│    └──────────┘  └──────────┘  └────────────────┘   │
│    ┌──────────────────────────────────────────────┐  │
│    │             Infrastructure Layer             │  │
│    │  PostgreSQL │  Local/IPFS Storage │  Web3   │  │
│    └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Ethereum Blockchain                     │
│   EvidenceRegistry.sol │ CustodyContract.sol        │
└─────────────────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Blockchain Registration** | Every uploaded file is hashed (SHA-256) and its hash registered on an Ethereum smart contract |
| **IPFS Storage** | Optional decentralised file storage alongside local filesystem |
| **Chain of Custody** | Every access, transfer, and verification is logged on-chain |
| **Integrity Verification** | Re-compute file hash and compare against blockchain at any time |
| **Role-Based Access** | Admin, Investigator, Officer, Analyst, Auditor roles with fine-grained permissions |
| **JWT Authentication** | Access + refresh token flow with server-side blacklisting |
| **Async Architecture** | Fully async FastAPI + SQLAlchemy 2.0 for high concurrency |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your secrets
```

### 2. Start all services

```bash
cd docker
docker compose up --build
```

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Access the application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |
| ReDoc | http://localhost:8000/api/redoc |
| IPFS Gateway | http://localhost:8080 |
| Blockchain RPC | http://localhost:8545 |

---

## Smart Contract Deployment

Contracts are located in `backend/core/infrastructure/blockchain/smart_contracts/`.

Using Hardhat:

```bash
cd hardhat-project
npx hardhat compile
npx hardhat run scripts/deploy.js --network localhost
```

After deployment, update `.env`:
```
EVIDENCE_REGISTRY_CONTRACT_ADDRESS=0x...
CUSTODY_CONTRACT_ADDRESS=0x...
```

---

## Running Tests

```bash
# Backend unit + integration tests
cd blockchain-evidence-preservation-system
pip install -r requirements.txt
pytest backend/tests/ -v --cov=backend

# Frontend
cd frontend
npm install
npm run test
```

---

## Security Notes

- All file uploads are MIME-verified using libmagic (prevents extension spoofing)
- Passwords are hashed with bcrypt (12 rounds)
- JWT secrets must be at least 64 characters in production
- The `.env` file is gitignored — never commit secrets
- Smart contracts use role-based access (OFFICER_ROLE required to register evidence)
- Evidence soft-deletion preserves the blockchain record — it is immutable

---

## Evidence Lifecycle

```
Upload → Hash → Store → IPFS Pin → Blockchain Register → Custody Log
   ↓
Verify → Re-hash → Compare DB hash → Compare blockchain hash
   ↓
Transfer → Custody entry on-chain → New officer recorded
```
