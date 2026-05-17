
BEPS — Blockchain Evidence Preservation System
==============================================

A full-stack system for secure digital evidence management using blockchain.

Tech Stack:
- FastAPI (Python) backend
- Vue.js frontend
- PostgreSQL database
- Hardhat Ethereum blockchain
- Docker containerization

----------------------------------------------
FEATURES
----------------------------------------------
- Evidence upload and hashing
- Blockchain immutability
- Role-based access control
- Case management workflow
- Audit trail system
- JWT authentication
- Swagger API docs
- Optional IPFS support

----------------------------------------------
SYSTEM ARCHITECTURE
----------------------------------------------
Frontend (Vue.js)
        ↓
Backend (FastAPI)
        ↓
PostgreSQL + Blockchain (Hardhat)
        ↓
Optional IPFS

----------------------------------------------
PREREQUISITES
----------------------------------------------
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker & Docker Compose
- Git

----------------------------------------------
QUICK START (DOCKER)
----------------------------------------------
1. Clone repo
   git clone <repo-url>
   cd blockchain-evidence-preservation-system

2. Copy environment file
   cp .env.example .env

3. Start system
   cd docker
   docker compose up --build

4. Run migrations
   docker compose exec backend alembic upgrade head

5. Open app
   Frontend: http://localhost:5173
   API Docs: http://localhost:8000/api/docs

----------------------------------------------
MANUAL SETUP SUMMARY
----------------------------------------------
Backend:
- python -m venv .venv
- pip install -r requirements.txt
- uvicorn app.main:app --reload

Database:
- Create PostgreSQL DB beps_db

Blockchain:
- npx hardhat node
- npx hardhat run scripts/deploy.js

Frontend:
- npm install
- npm run dev

----------------------------------------------
DEFAULT URLS
----------------------------------------------
Frontend: http://localhost:5173
Backend: http://localhost:8000
Docs: http://localhost:8000/api/docs
Blockchain RPC: http://localhost:8545

----------------------------------------------
NOTES
----------------------------------------------
- Always update .env secrets in production
- Contract addresses change after redeploy
- Hardhat is for development only

