# PCI Operation Optimization

Full-stack web application for PCI (Process Control Inspection) operation optimization. Manages crate offloading, shipping assumptions, COA (Certificate of Analysis), daily analysis dashboards, risk management, and configuration data.

## Tech Stack

**Frontend:** React 19, Vite, TypeScript, TailwindCSS 4, Radix UI, ECharts, TanStack Query/Table

**Backend:** FastAPI, SQLAlchemy, Alembic, APScheduler, PostgreSQL

**Auth:** Azure AD SSO + LDAP + JWT

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (running on port 5433)

## Setup

### 1. PostgreSQL

Create a database:
```sql
CREATE DATABASE pci_optimization;
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database URL and Azure AD settings

# Run migrations
alembic upgrade head

# Seed initial data
python -m app.seed

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend

```bash
cd frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with Azure AD client ID and tenant ID

# Start dev server
npm run dev
```

Visit http://localhost:8080

## Default Credentials

- **Admin:** admin / admin123
- **SSO:** Use Corning Azure AD account (requires PCI-Optimization-Access AD group membership)

## Project Structure

```
backend/
├── app/
│   ├── config.py           # Pydantic settings
│   ├── database.py         # SQLAlchemy engine
│   ├── dependencies.py     # FastAPI dependencies (auth, DB)
│   ├── main.py             # App entry point
│   ├── models/             # SQLAlchemy models
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── etl/                # ETL jobs (scheduler + sync)
│   └── utils/              # Security, Azure AD, LDAP
├── alembic/                # Database migrations
└── requirements.txt

frontend/
├── src/
│   ├── components/         # Shared UI components
│   ├── features/           # Feature modules
│   │   ├── auth/           # Authentication
│   │   ├── offload/        # PCI Offload
│   │   ├── shipping/       # Shipping Assumption
│   │   ├── coa/            # COA
│   │   ├── daily-analysis/ # ML/MSL/Attribute charts
│   │   ├── risk/           # Risk Management
│   │   ├── data-mgmt/      # Data Management
│   │   └── admin/          # Admin dashboard
│   ├── lib/                # API client, utilities
│   └── pages/              # Legacy placeholder pages
├── vite.config.ts
└── package.json
```

## Ports

| Service    | Port |
|-----------|------|
| Frontend  | 8080 |
| Backend   | 8001 |
| PostgreSQL| 5433 |

## ETL Schedule

Daily ETL runs at 06:00-06:45 (configurable):
- 06:00 — Batch sync (MESDW → PostgreSQL)
- 06:15 — Defect sync (Oracle PPDA → PostgreSQL)
- 06:30 — Cube MSL sync (SSAS → PostgreSQL)
- 06:45 — Shipping import (Excel → PostgreSQL)

Manual trigger available via Admin dashboard.

## Permissions

| Role   | Capabilities |
|--------|-------------|
| Admin  | Full access + user management + ETL control |
| Editor | Offload selection, shipping, COA (basic operations) |
| Viewer | Read-only access |

Feature permissions (additive):
- `offload_override` — Select non-compliant crates
- `data_mgmt` — Manage configuration data
- `risk_mgmt` — Create/modify risk rules
