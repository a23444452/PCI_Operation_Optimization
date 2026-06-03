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
- Access to Corning AD domain (ap.corning.com)
- Network access to Oracle PPDA, MESDW SQL Server, SSAS Cube (for ETL)

## Quick Start

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

# Seed initial data (plants, tanks, items, admin user)
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

---

## Feature Modules

### 1. PCI Offload

**Purpose:** Evaluate crates against defect criteria and decide whether to offload (reject) or pass them.

**Business Logic:**
- Each plant defines defect criteria (e.g., Blister > 100um, Platinum > 50um, Crystalline Pt > 40um)
- System pulls defect inspection data from Oracle PPDA and calculates defect ratios per crate
- Crates exceeding any criterion threshold are flagged as non-compliant
- Operators select which crates to offload; non-compliant selections require `offload_override` permission

**Usage:**
1. Select a plant from the dropdown
2. Review the crate list — each row shows defect ratios and compliance status
3. Green indicators = within spec; Red = exceeds threshold
4. Check crates to offload, then click "Confirm Selection"
5. If selecting a non-compliant crate, the system prompts for override justification (requires permission)

**Key Defect Types:**
| Code | Name | Description |
|------|------|-------------|
| 1 | Blister | Gas bubble in glass |
| 3 | Platinum | Platinum particle inclusion |
| 5 | Surface Blister | Surface-level gas bubble |
| 6 | Needle Pt | Needle-shaped platinum |
| 7 | Crystalline Pt | Crystalline platinum inclusion |

---

### 2. Shipping Assumption

**Purpose:** Assign crates to shipping schedules using FIFO (First In, First Out) logic.

**Business Logic:**
- Shipping schedules define target ship dates and required quantities
- FIFO cutoff rule: `cut_lot_end_date <= (ship_date - 3 days)`
  - Only crates that finished cutting at least 3 days before ship date are eligible
- Eligible crates are sorted by `cut_lot_end_date` ascending (oldest first)
- System assigns crates to schedules until quantity is fulfilled

**Usage:**
1. View all shipping schedules with their fulfillment status
2. Click a schedule to expand and see assigned crates
3. Progress bars show fulfillment percentage
4. Click "Recalculate" to re-run FIFO assignment (e.g., after new crates arrive)
5. Export assignments for logistics coordination

**FIFO Example:**
```
Ship Date: 2026-06-10
Cutoff: 2026-06-07 (ship_date - 3 days)

Eligible crates (cut_lot_end_date <= 2026-06-07):
  Crate A: cut 2026-06-01 ✓ (assigned first)
  Crate B: cut 2026-06-05 ✓ (assigned second)
  Crate C: cut 2026-06-08 ✗ (too recent, not eligible)
```

---

### 3. COA (Certificate of Analysis)

**Purpose:** Generate COA reports combining defect ratios and MSL (Mechanical Stress Level) data per crate.

**Business Logic:**
- Defect data comes from Oracle PPDA (via ETL)
- MSL data comes from SSAS Cube (via ETL)
- COA combines both into a unified quality report per crate
- Supports Excel export for customer delivery

**Usage:**
1. Filter by date range and plant
2. View combined defect + MSL data in a table
3. Columns include: crate ID, Gen, all defect ratios, MSL metrics, composite scores
4. Click "Export Excel" to download formatted COA spreadsheet

**Composite Columns:**
- `NG(Pt_CPt_SD)<6%` — Sum of blister, other, SBL, needle Pt, Pt, crystalline Pt (must be < 6%)
- `ADG` — Sum of A-side and B-side adhered glass

**MSL Columns:**
- A-Crack, A-Drip, A-ADG, A-SC, A-Stain
- B-Drip, B-Stain, B-SC, B-Crack, B-ADG
- Full Sheet Broken

---

### 4. Daily Analysis

**Purpose:** Visualize quality trends over time with stacked bar charts, grouped by tank.

Three sub-tabs:

#### 4a. ML (Melting Loss)

Tracks melting-related defect metrics per tank over time.

#### 4b. MSL (Mechanical Stress Level)

Tracks mechanical stress metrics from the SSAS Cube data per tank.

#### 4c. Attribute

Tracks attribute-level quality metrics per tank over time.

**Chart Format:**
- One stacked bar chart per tank
- X-axis: date
- Y-axis: defect loss percentage
- Each stack segment represents one crate's contribution to that day's total
- Hover to see individual crate details

**Usage:**
1. Select the sub-tab (ML / MSL / Attribute)
2. Choose date range (default: last 30 days)
3. Charts auto-populate for all active tanks
4. Click on a bar segment to drill down to crate details

---

### 5. Risk Management

**Purpose:** Flag high-risk crates based on configurable rules and track risk levels.

**Risk Levels:**
- **High** (Red) — Immediate attention required
- **Medium** (Yellow) — Monitor closely
- **Low** (Green) — Informational

**Usage:**
1. View risk crates grouped by level
2. Filter by risk level using level buttons
3. Click a crate to see which rules triggered the flag
4. Create/edit risk rules (requires `risk_mgmt` permission):
   - Define condition (e.g., "Platinum ratio > 5%")
   - Set severity level
   - Enable/disable rules

---

### 6. Data Management

**Purpose:** CRUD management for all configuration entities used across the system.

**Sub-tabs:**
| Entity | Description |
|--------|-------------|
| Plants | Production plant definitions (e.g., TC) |
| Plant Criteria | Defect thresholds per plant (e.g., Blister > 100um for TC) |
| Tanks | Forming tanks within plants |
| ML Items | Melting Loss item definitions |
| MSL Items | Mechanical Stress Level item definitions |
| Attribute Items | Attribute quality item definitions |

**Usage:**
1. Select a sub-tab for the entity type
2. View all records in a sortable/filterable table
3. Click "Add" to create a new record
4. Click the edit icon to modify an existing record
5. Click the delete icon to remove (with confirmation)
6. All changes take effect immediately

**Requires:** `data_mgmt` permission

---

### 7. Admin Dashboard

**Purpose:** System administration including ETL management and user approval.

**ETL Management:**
- View status of all 4 ETL jobs (last run time, status, row count)
- Manually trigger any ETL job
- View error logs for failed jobs

**User Management:**
- Approve/reject pending SSO registrations
- Assign roles (admin/editor/viewer)
- Grant feature permissions (offload_override, data_mgmt, risk_mgmt)
- Deactivate users

**Requires:** `admin` role

---

## Authentication

### Login Methods

1. **Azure AD SSO (Recommended)**
   - Click "Sign in with Corning Account"
   - Authenticates via Azure AD
   - Validates membership in AD group: `PCI-Optimization-Access`
   - First-time users are registered with "pending" status (requires admin approval)

2. **Local Account**
   - Username/password login
   - Passwords hashed with bcrypt
   - Rate limited to 5 attempts/minute

### Token Flow

```
Login → Access Token (JWT, expires in 8h)
     → Refresh Token (HttpOnly cookie, expires in 7d)

API Request → Bearer token in Authorization header
Token Expired → POST /api/v1/auth/refresh → New access token
```

---

## Permissions

### Roles

| Role | Capabilities |
|------|-------------|
| Admin | Full access + user management + ETL control |
| Editor | Offload selection, shipping, COA (basic operations) |
| Viewer | Read-only access to all dashboards |

### Feature Permissions (additive)

| Permission Key | Grants |
|---------------|--------|
| `offload_override` | Select non-compliant crates for offload |
| `data_mgmt` | Create/modify/delete configuration data |
| `risk_mgmt` | Create/modify risk rules |

Admins have all permissions implicitly.

---

## ETL (Data Pipeline)

### Schedule

Daily ETL runs automatically (configurable in `.env`):

| Time | Job | Source | Description |
|------|-----|--------|-------------|
| 06:00 | Batch Sync | MESDW (SQL Server) | Crate batches, cut dates, quantities |
| 06:15 | Defect Sync | Oracle PPDA | Defect inspection results |
| 06:30 | Cube MSL Sync | SSAS Cube | Mechanical stress level data |
| 06:45 | Shipping Import | Shared Folder (Excel) | Shipping schedules from logistics |

### Data Sources

| Source | Connection | Data |
|--------|-----------|------|
| Oracle PPDA | `oracle+oracledb://training:training@TC_PPDA` | Defect inspection data |
| MESDW | `mssql+pyodbc://TCF11SQL2011/MESDW` (Windows Auth) | Batch/crate metadata |
| SSAS Cube | `Provider=MSOLAP;Data Source=cgtppd;Catalog=ppd` | MSL aggregated data |
| Excel Files | Configured folder path | Shipping schedules |

### Manual Trigger

Admin users can manually trigger any ETL job from the Admin dashboard. Useful for:
- Re-importing after source data corrections
- Testing connectivity
- Off-schedule data refreshes

---

## API Reference

Base URL: `http://localhost:8001/api/v1`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Local username/password login |
| POST | `/auth/sso-login` | Azure AD SSO login |
| POST | `/auth/sso-register` | Register new SSO user (pending approval) |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |

### Offload

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/offload/plants` | List all plants |
| GET | `/offload/plants/{id}/crates` | Evaluate crates for a plant |
| POST | `/offload/selections` | Create offload selection |
| GET | `/offload/selections` | List past selections |

### Shipping

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/shipping/schedules` | List shipping schedules |
| GET | `/shipping/schedules/{id}/assignments` | Get crate assignments |
| POST | `/shipping/schedules/{id}/recalculate` | Re-run FIFO assignment |

### COA

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/coa/data` | Get COA data (defects + MSL) |
| GET | `/coa/export` | Download Excel COA report |

### Daily Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analysis/tanks` | List tanks |
| GET | `/analysis/items/{type}` | List items (ml/msl/attribute) |
| GET | `/analysis/ml` | ML chart data |
| GET | `/analysis/msl` | MSL chart data |
| GET | `/analysis/attribute` | Attribute chart data |

### Risk

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/risk/crates` | Risk crates by level |
| GET | `/risk/rules` | List risk rules |
| POST | `/risk/rules` | Create risk rule |
| PUT | `/risk/rules/{id}` | Update risk rule |
| DELETE | `/risk/rules/{id}` | Delete risk rule |

### Data Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/data-management/plants` | List/Create plants |
| PUT/DELETE | `/data-management/plants/{id}` | Update/Delete plant |
| GET/POST | `/data-management/criteria` | List/Create criteria |
| PUT/DELETE | `/data-management/criteria/{id}` | Update/Delete criteria |
| GET/POST | `/data-management/tanks` | List/Create tanks |
| PUT/DELETE | `/data-management/tanks/{id}` | Update/Delete tank |
| GET/POST | `/data-management/ml-items` | List/Create ML items |
| PUT/DELETE | `/data-management/ml-items/{id}` | Update/Delete ML item |
| GET/POST | `/data-management/msl-items` | List/Create MSL items |
| PUT/DELETE | `/data-management/msl-items/{id}` | Update/Delete MSL item |
| GET/POST | `/data-management/attribute-items` | List/Create attribute items |
| PUT/DELETE | `/data-management/attribute-items/{id}` | Update/Delete attribute item |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/etl/status` | ETL job statuses |
| POST | `/admin/etl/trigger/{job_name}` | Manually trigger ETL job |
| GET | `/admin/users` | List all users |
| PUT | `/admin/users/{id}` | Update user role/status/permissions |

---

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/pci_optimization

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXPIRY_HOURS=8
JWT_REFRESH_EXPIRY_DAYS=7

# Azure AD
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_TENANT_ID=your-tenant-id
AD_REQUIRED_GROUP=PCI-Optimization-Access

# LDAP Service Account
LDAP_BIND_DN=corning.com\\svc_pci_app
LDAP_BIND_PASSWORD=service-account-password

# ETL Sources
PPDA_CONN=oracle+oracledb://training:training@TC_PPDA
MESDW_CONN=mssql+pyodbc://TCF11SQL2011/MESDW?Trusted_Connection=yes&driver=SQL+Server
CUBE_CONN=Provider=MSOLAP;Data Source=cgtppd;Catalog=ppd;
ADOMD_DLL_PATH=C:\path\to\Microsoft.AnalysisServices.AdomdClient.dll
SHIPPING_FOLDER=\\\\server\\share\\shipping

# ETL Toggle
ETL_ENABLED=true
```

### Frontend (.env)

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_AZURE_AD_CLIENT_ID=your-client-id
VITE_AZURE_AD_TENANT_ID=your-tenant-id
```

---

## Project Structure

```
backend/
├── app/
│   ├── config.py           # Pydantic settings (from .env)
│   ├── database.py         # SQLAlchemy engine & session
│   ├── dependencies.py     # FastAPI deps (auth, DB, permissions)
│   ├── main.py             # App entry point + lifespan
│   ├── seed.py             # Initial data seeding
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── user.py         # User + UserPermission
│   │   ├── offload.py      # Plant, PlantCriteria, OffloadSelection
│   │   ├── shipping.py     # ShippingSchedule, ShippingAssignment
│   │   ├── analysis.py     # Tank, MlItem, MslItem, AttributeItem, AnalysisData
│   │   ├── risk.py         # RiskRule, RiskCrate
│   │   └── etl.py          # EtlJob (execution log)
│   ├── routers/            # API endpoint definitions
│   │   ├── auth.py         # Authentication (login, SSO, refresh)
│   │   ├── offload.py      # PCI Offload operations
│   │   ├── shipping.py     # Shipping FIFO logic
│   │   ├── coa.py          # COA data + Excel export
│   │   ├── analysis.py     # Daily analysis chart data
│   │   ├── risk.py         # Risk management
│   │   ├── data_management.py  # Config CRUD
│   │   └── admin.py        # ETL + user management
│   ├── schemas/            # Pydantic request/response schemas
│   ├── services/           # Business logic layer
│   │   ├── auth_service.py
│   │   ├── offload_service.py
│   │   └── shipping_service.py
│   ├── etl/                # ETL jobs + scheduler
│   │   ├── scheduler.py    # APScheduler cron config
│   │   ├── connections.py  # Oracle + MSSQL context managers
│   │   ├── batch_sync.py   # MESDW → PostgreSQL
│   │   ├── defect_sync.py  # Oracle PPDA → PostgreSQL
│   │   ├── cube_sync.py    # SSAS Cube → PostgreSQL
│   │   └── shipping_import.py  # Excel → PostgreSQL
│   ├── middleware/         # Rate limiting
│   └── utils/              # Security, Azure AD, LDAP
├── alembic/                # Database migrations
├── requirements.txt
└── .env.example

frontend/
├── src/
│   ├── App.tsx             # Root: MSAL + Auth + Router
│   ├── components/         # Shared UI (layout, tables, forms)
│   ├── features/           # Feature modules
│   │   ├── auth/           # Login page + SSO flow
│   │   ├── offload/        # PCI Offload tab
│   │   ├── shipping/       # Shipping Assumption tab
│   │   ├── coa/            # COA tab
│   │   ├── daily-analysis/ # ML/MSL/Attribute charts
│   │   ├── risk/           # Risk Management tab
│   │   ├── data-mgmt/      # Data Management tab
│   │   └── admin/          # Admin dashboard
│   ├── lib/                # API client, auth context, utilities
│   └── hooks/              # Custom React hooks
├── vite.config.ts
├── tailwind.config.ts
└── package.json
```

---

## Ports

| Service | Port |
|---------|------|
| Frontend | 8080 |
| Backend | 8001 |
| PostgreSQL | 5433 |

---

## Deployment (Windows Server)

### Production Setup

1. **PostgreSQL**: Install and configure on port 5433
2. **Backend**: Run with production ASGI server
   ```bash
   pip install gunicorn uvicorn[standard]
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
   ```
3. **Frontend**: Build and serve with nginx or IIS
   ```bash
   cd frontend
   npm run build
   # Deploy dist/ folder to web server
   ```
4. **ETL**: Ensure network access to Oracle, MSSQL, SSAS from the server
5. **Windows Service**: Use NSSM or Task Scheduler to run backend as a service

### Network Requirements

| Source | Destination | Port | Protocol |
|--------|------------|------|----------|
| Backend | PostgreSQL | 5433 | TCP |
| Backend | Oracle PPDA | 1521 | TCP |
| Backend | MESDW SQL Server | 1433 | TCP |
| Backend | SSAS Cube (cgtppd) | 2383 | TCP |
| Backend | AD (ap.corning.com) | 636 | LDAPS |
| Frontend | Backend | 8001 | HTTP |
| Users | Frontend | 8080 | HTTP |

---

## Troubleshooting

### Common Issues

**"LDAP bind failed"**
- Verify service account credentials in `.env`
- Check network access to ap.corning.com:636
- Ensure the user is in the correct OU under DC=ap,DC=corning,DC=com

**"ETL job failed"**
- Check Admin dashboard for error details
- Verify source database connectivity
- For SSAS Cube: ensure ADOMD DLL path is correct
- For shipping import: verify Excel file format matches expected schema

**"Token expired"**
- The frontend automatically refreshes tokens
- If refresh fails, user will be redirected to login
- Check that JWT_SECRET hasn't changed between sessions

**"Permission denied"**
- Verify user role and feature permissions in Admin dashboard
- Admin role has all permissions implicitly
- Feature permissions (offload_override, data_mgmt, risk_mgmt) must be explicitly granted

**Python 3.13+ MD4 Error**
- The system includes a pure-Python MD4 fallback for NTLM authentication
- This activates automatically when OpenSSL 3.0+ removes MD4 support
- No action needed — the monkey-patch handles it transparently

---

## Development

### Running Tests

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

### API Documentation

FastAPI auto-generates interactive docs:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## Legacy Config Reference

The root-level `config.py` contains legacy configuration that was used before the web system. It documents the domain knowledge:

- **DEFECT_DICT**: Defect type code-to-name mapping (0-8)
- **RECEIVER_SPECS**: Customer-specific defect thresholds (e.g., TC plant criteria)
- **DEFECT_SHORT_NAMES**: Cube defect ID abbreviations (e.g., "A-side adhered glass full sheet" → "A-ADG")
- **MSL_COLUMNS**: Standard MSL column order for reports
- **COMPOSITE_COLUMNS**: Calculated columns that sum multiple defect types
- **CUBE_RENAME / CUBE_DEFECT_COL / CUBE_VALUE_COL**: SSAS Cube MDX column mappings

This configuration has been migrated into the web system's database (managed via Data Management tab) but the file remains as domain reference.
