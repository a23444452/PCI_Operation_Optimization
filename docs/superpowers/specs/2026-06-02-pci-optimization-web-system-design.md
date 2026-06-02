# PCI Operation Optimization — Web UI System Design Spec

## Overview

A full-stack web application for PCI (Particle/Defect Inspection) operation optimization at Corning. The system automates defect data collection via daily ETL, provides offload decision support, shipping schedule management, COA generation, daily analysis dashboards, and risk management for 20-30 production line users.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + TypeScript + TailwindCSS 4 + Radix UI + ECharts + TanStack (Table/Query) |
| Backend | FastAPI + SQLAlchemy + Alembic (migrations) + APScheduler |
| Database | PostgreSQL (local cache DB) |
| Auth | Azure AD SSO + LDAP + JWT (same as Dt_Quality_Roadmap) |
| External Data | Oracle (PPDA) + MSSQL (MESDW) + SSAS Cube + Shared Folder (Excel) |
| Deployment | Windows Server (direct execution, no Docker) |

## Port Configuration

| Service | Port | Notes |
|---------|------|-------|
| Frontend (Vite) | 8080 | Avoids conflict with Dt_Quality_Roadmap (80/5173) |
| Backend (FastAPI) | 8001 | Avoids conflict with Dt_Quality_Roadmap (8000) |
| PostgreSQL | 5433 | Non-default to avoid conflicts |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Windows Server                            │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │     Backend      │    │  PostgreSQL  │  │
│  │  React+Vite  │───▶│    FastAPI       │───▶│   Local DB   │  │
│  │  port:8080   │    │   port:8001      │    │  port:5433   │  │
│  └──────────────┘    │                  │    └──────┬───────┘  │
│                      │  ┌────────────┐  │           │          │
│                      │  │APScheduler │  │           │          │
│                      │  │ Daily ETL  │  │           │          │
│                      │  └─────┬──────┘  │           │          │
│                      └────────┼─────────┘           │          │
│                               │                     │          │
└───────────────────────────────┼─────────────────────┼──────────┘
                                │ (Daily schedule)     │
                    ┌───────────▼───────────────┐     │
                    │  Oracle / MSSQL / Cube /   │     │
                    │  Shared Folder (Excel)     │     │
                    └───────────────────────────┘     │
```

### Data Flow

1. **APScheduler** triggers daily ETL job each morning
2. ETL pulls new data from Oracle/MSSQL/Cube → writes to PostgreSQL
3. ETL also fetches Planner's shipping schedule Excel from shared folder → parses into PostgreSQL
4. Users query via Frontend → FastAPI reads only from PostgreSQL → fast response

---

## Database Schema (PostgreSQL)

### Users & Permissions

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',  -- admin, editor, viewer
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, active, inactive
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    feature_key VARCHAR(50) NOT NULL,  -- offload_override, data_mgmt, risk_mgmt
    UNIQUE(user_id, feature_key)
);
```

### ETL Cached Data

```sql
CREATE TABLE batches (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL,
    crate_id VARCHAR(50),
    in_qty INTEGER,
    cut_lot_end_date DATE,
    etl_date DATE NOT NULL,
    UNIQUE(batch_id, crate_id)
);

CREATE TABLE defects (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) NOT NULL,
    sheet_id VARCHAR(50),
    line_id VARCHAR(20),
    x_position FLOAT,
    y_position FLOAT,
    loss_code VARCHAR(20),
    lis_defect_type VARCHAR(50),
    defect_size FLOAT,
    etl_date DATE NOT NULL
);

CREATE TABLE cube_msl (
    id SERIAL PRIMARY KEY,
    crate_id VARCHAR(50) NOT NULL,
    gen VARCHAR(20),
    defect_item VARCHAR(100),
    value FLOAT,
    etl_date DATE NOT NULL
);
```

### Offload

```sql
CREATE TABLE plants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE plant_criteria (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER REFERENCES plants(id) ON DELETE CASCADE,
    defect_type VARCHAR(50) NOT NULL,
    min_size FLOAT,
    operator VARCHAR(10) NOT NULL DEFAULT '<',  -- <, <=, >, >=
    threshold FLOAT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE offload_selections (
    id SERIAL PRIMARY KEY,
    crate_id VARCHAR(50) NOT NULL,
    plant_id INTEGER REFERENCES plants(id),
    selected_by INTEGER REFERENCES users(id),
    selected_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'selected',  -- selected, shipped, cancelled
    is_override BOOLEAN DEFAULT FALSE  -- TRUE if crate doesn't meet criteria
);
```

### Shipping

```sql
CREATE TABLE shipping_schedules (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER REFERENCES plants(id),
    target_qty INTEGER NOT NULL,
    ship_date DATE NOT NULL,
    source_file VARCHAR(255),
    imported_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE shipping_assignments (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES shipping_schedules(id) ON DELETE CASCADE,
    crate_id VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    priority_order INTEGER NOT NULL  -- FIFO order
);
```

### Daily Analysis

```sql
CREATE TABLE daily_ml (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER REFERENCES tanks(id),
    crate_id VARCHAR(50),
    date DATE NOT NULL,
    item_name VARCHAR(50) NOT NULL,
    value FLOAT,
    etl_date DATE NOT NULL
);

CREATE TABLE daily_msl (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER REFERENCES tanks(id),
    crate_id VARCHAR(50),
    date DATE NOT NULL,
    item_name VARCHAR(50) NOT NULL,
    value FLOAT,
    etl_date DATE NOT NULL
);

CREATE TABLE daily_attribute (
    id SERIAL PRIMARY KEY,
    tank_id INTEGER REFERENCES tanks(id),
    crate_id VARCHAR(50),
    date DATE NOT NULL,
    item_name VARCHAR(50) NOT NULL,
    value FLOAT,
    etl_date DATE NOT NULL
);
```

### Risk Management

```sql
CREATE TABLE risk_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    conditions_json JSONB NOT NULL,  -- flexible rule definition
    risk_level VARCHAR(10) NOT NULL,  -- H, M, L
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    crate_id VARCHAR(50) NOT NULL,
    risk_level VARCHAR(10) NOT NULL,
    rule_id INTEGER REFERENCES risk_rules(id),
    assessed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT
);
```

### Data Management (Configurable Items)

```sql
CREATE TABLE tanks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE ml_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE msl_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE attribute_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0
);
```

### ETL Job Tracking

```sql
CREATE TABLE etl_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,  -- batch_sync, defect_sync, cube_sync, shipping_import
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',  -- running, success, failed
    records_count INTEGER DEFAULT 0,
    error_msg TEXT
);
```

---

## Feature Specifications

### Tab 1: PCI Offload

**Purpose**: Let users select crates for shipping offload based on plant-specific criteria.

**Flow**:
1. User selects Plant from dropdown
2. System displays the plant's criteria (e.g., Blister ≥ 100μm: < 2%)
3. System queries PostgreSQL for available crates and evaluates against criteria
4. Table displays all crates with pass/fail indicators:
   - Passing crates: selectable by all Editors
   - Failing crates: only selectable by Admin / Editor with `offload_override` permission
   - Failing items highlighted in red
5. User checks crates to offload → clicks "Confirm"
6. Selected crates saved to `offload_selections`

**UI Elements**:
- Dropdown: Plant selector
- Info panel: Current plant criteria
- Table: Crate list with checkbox, Gen, defect ratios, in_qty
- Color coding: red for exceeding threshold
- Lock icon on non-compliant crates for unauthorized users
- Button: "Confirm Offload"

---

### Tab 2: Shipping Assumption

**Purpose**: Auto-assign crates to shipping schedules based on Planner's Excel and FIFO rules.

**Data Input**: System fetches Planner's Excel from shared folder at scheduled time.

**FIFO Logic**:
- Pool condition: `cut_lot_end_date ≤ (ship_date - 3 days)` AND meets plant criteria AND not yet assigned
- Sort by `cut_lot_end_date` ASC (earliest first), then by `crate_id`
- Accumulate `in_qty` until `target_qty` is reached
- Surplus crates (beyond target) → routed to Risk Management (L-risk)

**UI Elements**:
- Summary table: Ship Date | Plant | Target Qty | Assigned Qty | Gap
- Status indicators: ✅ (met), ⚠️ (shortfall)
- Expandable rows showing FIFO-assigned crate list
- Display source file name and import timestamp

---

### Tab 3: COA (Certificate of Analysis)

**Purpose**: Generate defect/MSL data table for selected offload crates, for review and Excel export.

**Flow**:
1. Automatically displays crates selected in PCI Offload tab
2. Shows comprehensive table: crate_id, Gen, all defect ratios, all MSL items
3. User reviews data
4. Click "Export Excel" → downloads formatted COA spreadsheet

**UI Elements**:
- Table: Full defect ratio + MSL data for selected crates
- Button: "Export Excel"
- Filter/search within the table

---

### Tab 4: Daily Analysis — ML (Material Loss)

**Purpose**: Visualize Material Loss trends per tank over time.

**UI Elements**:
- Dropdown: ML Item selector (Blister, C-Pt, Inclusion, N-Pt, Pt, SBL, SD, Zr, Other)
- Multiple stacked bar charts (one per active Tank)
- Each chart: X-axis = date, Y-axis = value, stacked by crate contribution
- Charts update dynamically when dropdown selection changes

---

### Tab 5: Daily Analysis — MSL (Material Surface Loss)

**Purpose**: Same as Tab 4 but for MSL items.

**UI Elements**: Same structure as Tab 4.
- Dropdown: MSL Item selector (Cord, etc.)
- One stacked chart per Tank

---

### Tab 6: Daily Analysis — Attribute

**Purpose**: Same as Tab 4 but for Attribute items.

**UI Elements**: Same structure as Tab 4.
- Dropdown: Attribute Item selector (~30 items including MAX_THICKNESS, BOW_RANGE, WAVINESS, etc.)
- One stacked chart per Tank

---

### Tab 7: Risk Management

**Purpose**: Categorize and display crates that don't meet offload criteria or exceed shipping demand.

**Sources of risk crates**:
1. Crates failing plant criteria (from PCI Offload evaluation)
2. Crates exceeding Planner's target quantity (surplus from Shipping Assumption)

**Risk Levels**:
- H-risk (High): TBD — architecture supports configurable rules via `risk_rules` table
- M-risk (Medium): TBD
- L-risk (Low): e.g., surplus crates that pass all specs but exceed demand

**UI Elements**:
- Filter dropdown: All / H-risk / M-risk / L-risk
- Table grouped by risk level with color coding (🔴 🟡 🟢)
- Columns: Crate ID, Risk Level, Reason, Defect Details
- Expandable rows for full defect breakdown

---

### Tab 8: Data Management

**Purpose**: Admin/Editor interface for managing configurable system data.

**Manageable entities**:
- Plants (name, code, active status)
- Plant Criteria (per plant: defect type, min size, operator, threshold)
- Tanks (name, code, active status)
- ML Items (name, display name, active, sort order)
- MSL Items (name, display name, active, sort order)
- Attribute Items (name, display name, active, sort order)
- Risk Rules (name, conditions JSON, risk level, active)

**UI Elements**:
- Sub-tab navigation for each entity type
- CRUD table with inline editing
- Add/Edit modal dialogs
- Requires `data_mgmt` permission

---

## Authentication & Authorization

### Auth Flow (same as Dt_Quality_Roadmap)

1. User clicks "Login with Corning SSO"
2. Frontend acquires Azure AD token via MSAL
3. Backend verifies token + checks AD group membership
4. If new user → registration flow (pending admin approval)
5. If existing active user → issue JWT access + refresh tokens

### Role-Based Access Control

| Feature | Admin | Editor + Permission | Editor (general) | Viewer |
|---------|:---:|:---:|:---:|:---:|
| PCI Offload — select compliant crates | ✅ | ✅ | ✅ | 👁 read-only |
| PCI Offload — select non-compliant crates | ✅ | ✅ `offload_override` | ❌ | ❌ |
| Shipping Assumption | ✅ | ✅ | ✅ | 👁 read-only |
| COA (export) | ✅ | ✅ | ✅ | 👁 read-only |
| Daily Analysis (ML/MSL/Attribute) | ✅ | ✅ | ✅ | ✅ |
| Risk Management (edit) | ✅ | ✅ `risk_mgmt` | 👁 read-only | 👁 read-only |
| Data Management | ✅ | ✅ `data_mgmt` | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |

### Permission Keys

- `offload_override` — Can select non-compliant crates when shipping target not met
- `data_mgmt` — Can access Data Management tab (CRUD operations)
- `risk_mgmt` — Can manage risk rules and assessments

---

## ETL & Scheduled Jobs

### Daily ETL (APScheduler)

| Job | Schedule | Source | Target |
|-----|----------|--------|--------|
| Batch/Crate sync | Daily 06:00 | MESDW (SQL Server) | `batches` table |
| Defect sync | Daily 06:15 | PPDA (Oracle) | `defects` table |
| Cube MSL sync | Daily 06:30 | SSAS Cube (MDX) | `cube_msl` table |
| Shipping import | Daily 06:45 | Shared Folder (Excel) | `shipping_schedules` table |
| Risk assessment | Daily 07:00 | Internal (PostgreSQL) | `risk_assessments` table |

### ETL Strategy

- **Incremental**: Only fetch data newer than last successful ETL (`etl_date`)
- **Idempotent**: Re-running same day overwrites same-day data safely
- **Tracked**: All jobs logged in `etl_jobs` table with status/error
- **Alerting**: Failed ETL jobs surface in admin dashboard

---

## Project Structure

```
PCI_Operation_Optimization/
├── frontend/
│   ├── src/
│   │   ├── components/         # Shared UI components
│   │   │   ├── ui/            # Radix/shadcn primitives
│   │   │   ├── layout/        # Sidebar, Header, etc.
│   │   │   └── charts/        # ECharts wrappers
│   │   ├── features/          # Feature-based modules
│   │   │   ├── auth/          # Login, SSO, registration
│   │   │   ├── offload/       # PCI Offload tab
│   │   │   ├── shipping/      # Shipping Assumption tab
│   │   │   ├── coa/           # COA tab
│   │   │   ├── daily-analysis/# ML, MSL, Attribute tabs
│   │   │   ├── risk/          # Risk Management tab
│   │   │   ├── data-mgmt/     # Data Management tab
│   │   │   └── admin/         # User management
│   │   ├── hooks/             # Custom React hooks
│   │   ├── lib/               # API client, utils
│   │   └── types/             # TypeScript type definitions
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── config.py          # Settings (env-based)
│   │   ├── database.py        # PostgreSQL connection
│   │   ├── dependencies.py    # DI (auth, db session)
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API route handlers
│   │   ├── services/          # Business logic
│   │   ├── etl/               # ETL jobs & data fetchers
│   │   │   ├── scheduler.py   # APScheduler setup
│   │   │   ├── batch_sync.py
│   │   │   ├── defect_sync.py
│   │   │   ├── cube_sync.py
│   │   │   └── shipping_import.py
│   │   ├── middleware/        # Rate limiting, etc.
│   │   └── utils/             # Security, LDAP, Azure AD, email
│   ├── alembic/               # DB migrations
│   ├── tests/
│   ├── requirements.txt
│   └── .env
├── config.py                  # Legacy (existing ETL queries)
├── utils/                     # Legacy (existing ETL logic — reuse in backend/etl/)
├── docs/
└── README.md
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| PostgreSQL as local cache | 20-30 concurrent users, complex queries, proper indexing support |
| APScheduler (not Celery) | Simple daily jobs, no distributed workers needed, less infra |
| Same tech stack as Dt_Quality_Roadmap | Team familiarity, code reuse (auth, UI components) |
| Port 8080/8001/5433 | Avoids conflict with co-located Dt_Quality_Roadmap on same server |
| Feature-level permissions | Flexible: same Editor role can have different feature access |
| FIFO with 3-day minimum age | Business rule: crates need 3+ days after completion before shipping |
| risk_rules as JSONB | Flexibility for undefined rules; can be made structured later |
| Reuse existing utils/ | Oracle/MSSQL/Cube query logic already works, integrate into ETL |

---

## Non-Functional Requirements

- **Response time**: < 2s for any query (data pre-cached in PostgreSQL)
- **Concurrent users**: 20-30 simultaneous
- **Data freshness**: Updated daily by 07:00
- **Availability**: Business hours (24/5 acceptable)
- **Browser support**: Chrome (latest), Edge (latest)
