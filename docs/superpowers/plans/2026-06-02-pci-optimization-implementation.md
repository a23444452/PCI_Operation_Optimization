# PCI Operation Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-stack web application for PCI operation optimization with daily ETL caching, 8 feature tabs, and role-based access control for 20-30 production line users.

**Architecture:** React 19 frontend communicates with FastAPI backend, which serves pre-cached data from PostgreSQL. APScheduler runs daily ETL jobs pulling from Oracle/MSSQL/SSAS Cube and a shared folder. Auth uses Azure AD SSO + LDAP + JWT (same as Dt_Quality_Roadmap).

**Tech Stack:** React 19, Vite, TypeScript, TailwindCSS 4, Radix UI, ECharts, TanStack Table/Query (frontend); FastAPI, SQLAlchemy, Alembic, APScheduler, psycopg2 (backend); PostgreSQL 5433 (database).

---

## Phase Overview

| Phase | Scope | Tasks |
|-------|-------|-------|
| 1 | Foundation: Project scaffolding, DB, Auth | Tasks 1–6 |
| 2 | ETL Layer: Scheduled jobs, data sync | Tasks 7–10 |
| 3 | Core Features: Offload, Shipping, COA | Tasks 11–16 |
| 4 | Analysis Dashboards: ML, MSL, Attribute | Tasks 17–19 |
| 5 | Risk & Data Management | Tasks 20–22 |

---

## Phase 1: Foundation

### Task 1: Backend Project Scaffolding

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/.env`

- [ ] **Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/{models,schemas,routers,services,etl,middleware,utils}
mkdir -p backend/tests
mkdir -p backend/alembic
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/routers/__init__.py
touch backend/app/services/__init__.py
touch backend/app/etl/__init__.py
touch backend/app/middleware/__init__.py
touch backend/app/utils/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```text
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.50
alembic==1.14.0
psycopg2-binary==2.9.10
pydantic-settings==2.7.0
python-jose[cryptography]==3.4.0
passlib[bcrypt]==1.7.4
slowapi==0.1.9
apscheduler==3.10.4
httpx==0.27.0
pandas==2.2.3
openpyxl==3.1.5
oracledb==2.5.1
pyodbc==5.2.0
pyadomd==0.1.1
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/pci_optimization"
    jwt_secret: str = "change-me-in-production"
    jwt_expiry_hours: int = 8
    jwt_refresh_expiry_days: int = 7
    cors_origins: str = "http://localhost:8080"
    azure_ad_client_id: str = ""
    azure_ad_tenant_id: str = ""
    ad_required_group: str = "PCI-Optimization-Access"
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    # ETL external connections
    ppda_conn: str = "oracle+oracledb://training:training@TC_PPDA"
    mesdw_conn: str = "mssql+pyodbc://TCF11SQL2011/MESDW?Trusted_Connection=yes&driver=SQL+Server"
    cube_conn: str = "Provider=MSOLAP;Data Source=cgtppd;Catalog=ppd;"
    adomd_dll_path: str = r"C:\Users\linp21"
    shipping_folder: str = r"\\server\shared\shipping"
    # Scheduler
    etl_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 4: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 5: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter

app = FastAPI(title="PCI Operation Optimization", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: Create .env.example and middleware**

`.env.example`:
```text
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/pci_optimization
JWT_SECRET=change-me-in-production
CORS_ORIGINS=http://localhost:8080
AZURE_AD_CLIENT_ID=
AZURE_AD_TENANT_ID=
ETL_ENABLED=true
SHIPPING_FOLDER=\\server\shared\shipping
```

`backend/app/middleware/rate_limit.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- [ ] **Step 7: Verify backend starts**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
# Visit http://localhost:8001/api/v1/health → {"status": "ok"}
```

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend with FastAPI + PostgreSQL config"
```

---

### Task 2: Database Models & Alembic Setup

**Files:**
- Create: `backend/app/models/base.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/plant.py`
- Create: `backend/app/models/batch.py`
- Create: `backend/app/models/defect.py`
- Create: `backend/app/models/cube_msl.py`
- Create: `backend/app/models/shipping.py`
- Create: `backend/app/models/daily_analysis.py`
- Create: `backend/app/models/risk.py`
- Create: `backend/app/models/etl_job.py`
- Create: `backend/app/models/data_management.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: Create base model mixin**

`backend/app/models/base.py`:
```python
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [ ] **Step 2: Create User model with permissions**

`backend/app/models/user.py`:
```python
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("feature_key", String(50), nullable=False),
)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="viewer", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    permissions: Mapped[list[str]] = []  # populated via query

    def has_permission(self, key: str) -> bool:
        return self.role == "admin" or key in self.permissions
```

- [ ] **Step 3: Create Plant, PlantCriteria, OffloadSelection models**

`backend/app/models/plant.py`:
```python
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Plant(TimestampMixin, Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    criteria: Mapped[list["PlantCriteria"]] = relationship(back_populates="plant", lazy="selectin")


class PlantCriteria(Base):
    __tablename__ = "plant_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id", ondelete="CASCADE"))
    defect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    min_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    operator: Mapped[str] = mapped_column(String(10), default="<", nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    plant: Mapped["Plant"] = relationship(back_populates="criteria")


class OffloadSelection(TimestampMixin, Base):
    __tablename__ = "offload_selections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    selected_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="selected")
    is_override: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 4: Create Batch, Defect, CubeMsl models**

`backend/app/models/batch.py`:
```python
from datetime import date

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Batch(Base):
    __tablename__ = "batches"
    __table_args__ = (UniqueConstraint("batch_id", "crate_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    crate_id: Mapped[str | None] = mapped_column(String(50), index=True)
    in_qty: Mapped[int | None] = mapped_column(Integer)
    cut_lot_end_date: Mapped[date | None] = mapped_column(Date)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
```

`backend/app/models/defect.py`:
```python
from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Defect(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sheet_id: Mapped[str | None] = mapped_column(String(50))
    line_id: Mapped[str | None] = mapped_column(String(20))
    x_position: Mapped[float | None] = mapped_column(Float)
    y_position: Mapped[float | None] = mapped_column(Float)
    loss_code: Mapped[str | None] = mapped_column(String(20))
    lis_defect_type: Mapped[str | None] = mapped_column(String(50))
    defect_size: Mapped[float | None] = mapped_column(Float)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
```

`backend/app/models/cube_msl.py`:
```python
from datetime import date

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CubeMsl(Base):
    __tablename__ = "cube_msl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    gen: Mapped[str | None] = mapped_column(String(20))
    defect_item: Mapped[str | None] = mapped_column(String(100))
    value: Mapped[float | None] = mapped_column(Float)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
```

- [ ] **Step 5: Create Shipping models**

`backend/app/models/shipping.py`:
```python
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShippingSchedule(Base):
    __tablename__ = "shipping_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"))
    target_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    ship_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(255))
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")

    assignments: Mapped[list["ShippingAssignment"]] = relationship(back_populates="schedule", lazy="selectin")


class ShippingAssignment(Base):
    __tablename__ = "shipping_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("shipping_schedules.id", ondelete="CASCADE"))
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    priority_order: Mapped[int] = mapped_column(Integer, nullable=False)

    schedule: Mapped["ShippingSchedule"] = relationship(back_populates="assignments")
```

- [ ] **Step 6: Create DailyAnalysis models**

`backend/app/models/daily_analysis.py`:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DailyMl(Base):
    __tablename__ = "daily_ml"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id"))
    crate_id: Mapped[str | None] = mapped_column(String(50))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)


class DailyMsl(Base):
    __tablename__ = "daily_msl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id"))
    crate_id: Mapped[str | None] = mapped_column(String(50))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)


class DailyAttribute(Base):
    __tablename__ = "daily_attribute"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tank_id: Mapped[int] = mapped_column(ForeignKey("tanks.id"))
    crate_id: Mapped[str | None] = mapped_column(String(50))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    item_name: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    etl_date: Mapped[date] = mapped_column(Date, nullable=False)
```

- [ ] **Step 7: Create Risk, DataManagement, EtlJob models**

`backend/app/models/risk.py`:
```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    conditions_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crate_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("risk_rules.id"))
    assessed_at: Mapped[datetime] = mapped_column(DateTime, server_default="now()")
    reason: Mapped[str | None] = mapped_column(Text)
```

`backend/app/models/data_management.py`:
```python
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Tank(Base):
    __tablename__ = "tanks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class MlItem(Base):
    __tablename__ = "ml_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class MslItem(Base):
    __tablename__ = "msl_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class AttributeItem(Base):
    __tablename__ = "attribute_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
```

`backend/app/models/etl_job.py`:
```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EtlJob(Base):
    __tablename__ = "etl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="running")
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str | None] = mapped_column(Text)
```

- [ ] **Step 8: Initialize Alembic and generate first migration**

```bash
cd backend
alembic init alembic
```

Edit `backend/alembic/env.py` to import all models and use `Base.metadata`:
```python
from app.database import Base
from app.models import user, plant, batch, defect, cube_msl, shipping, daily_analysis, risk, data_management, etl_job

target_metadata = Base.metadata
```

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: add all SQLAlchemy models + Alembic initial migration"
```

---

### Task 3: Authentication (Azure AD SSO + JWT)

**Files:**
- Create: `backend/app/utils/security.py`
- Create: `backend/app/utils/azure_ad.py`
- Create: `backend/app/utils/ldap_validation.py`
- Create: `backend/app/dependencies.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/routers/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Create security utilities (JWT)**

`backend/app/utils/security.py`:
```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {"sub": str(user_id), "role": role, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_expiry_days)
    payload = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
```

- [ ] **Step 2: Create dependencies (auth + permission checks)**

`backend/app/dependencies.py`:
```python
from collections.abc import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    from app.models.user import User, user_permissions
    from app.utils.security import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Load permissions
    perms = db.execute(
        user_permissions.select().where(user_permissions.c.user_id == user.id)
    ).fetchall()
    user.permissions = [p.feature_key for p in perms]
    return user


def require_role(*roles: str):
    def checker(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


def require_permission(feature_key: str):
    def checker(user=Depends(get_current_user)):
        if not user.has_permission(feature_key):
            raise HTTPException(status_code=403, detail=f"Permission '{feature_key}' required")
        return user
    return checker
```

- [ ] **Step 3: Create auth schemas and router**

`backend/app/schemas/common.py`:
```python
from typing import Any


def ok(data: Any = None):
    return {"success": True, "data": data}
```

`backend/app/schemas/auth.py`:
```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class SSOLoginRequest(BaseModel):
    access_token: str


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    role: str
    permissions: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    expires_in: int
    user: UserInfo
```

- [ ] **Step 4: Create auth router (login + SSO + refresh)**

`backend/app/routers/auth.py` — follow same pattern as Dt_Quality_Roadmap's auth.py with:
- `POST /api/v1/auth/login` — username/password login
- `POST /api/v1/auth/sso-login` — Azure AD token verification
- `POST /api/v1/auth/refresh` — JWT refresh
- `GET /api/v1/auth/me` — current user info

- [ ] **Step 5: Write auth tests**

```bash
cd backend
pytest tests/test_auth.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add authentication (Azure AD SSO + JWT + LDAP)"
```

---

### Task 4: User Management API

**Files:**
- Create: `backend/app/routers/users.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/tests/test_users.py`

- [ ] **Step 1: Create user schemas**

```python
from pydantic import BaseModel


class UserListItem(BaseModel):
    id: int
    username: str
    display_name: str
    email: str
    role: str
    status: str
    permissions: list[str] = []


class UpdateUserRole(BaseModel):
    role: str  # admin, editor, viewer


class UpdateUserStatus(BaseModel):
    status: str  # active, inactive, pending


class UpdateUserPermissions(BaseModel):
    permissions: list[str]  # offload_override, data_mgmt, risk_mgmt
```

- [ ] **Step 2: Create users router (Admin only)**

Endpoints:
- `GET /api/v1/users` — list all users (admin only)
- `PATCH /api/v1/users/{id}/role` — update role
- `PATCH /api/v1/users/{id}/status` — approve/deactivate
- `PUT /api/v1/users/{id}/permissions` — set feature permissions

- [ ] **Step 3: Test and commit**

```bash
pytest tests/test_users.py -v
git add backend/
git commit -m "feat: add user management API (admin only)"
```

---

### Task 5: Frontend Project Scaffolding

**Files:**
- Create: `frontend/` (Vite + React + TypeScript project)
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/components/layout/AppLayout.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create Vite project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
npm install @azure/msal-browser @azure/msal-react \
  @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-select \
  @radix-ui/react-checkbox @radix-ui/react-switch @radix-ui/react-tooltip \
  @radix-ui/react-separator @radix-ui/react-popover \
  @tailwindcss/vite tailwindcss tw-animate-css \
  @tanstack/react-query @tanstack/react-table \
  axios echarts echarts-for-react lucide-react \
  react-router-dom clsx class-variance-authority tailwind-merge
```

- [ ] **Step 3: Configure Vite (port 8080 + proxy)**

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 8080,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 4: Create API client**

`frontend/src/lib/api.ts`:
```typescript
import axios from "axios";

const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

- [ ] **Step 5: Create AppLayout with Sidebar (8 tabs)**

Sidebar navigation items:
1. PCI Offload
2. Shipping Assumption
3. COA
4. Daily Analysis — ML
5. Daily Analysis — MSL
6. Daily Analysis — Attribute
7. Risk Management
8. Data Management

- [ ] **Step 6: Setup routing with React Router**

```typescript
// Routes mapping to each feature tab
const routes = [
  { path: "/offload", element: <OffloadPage /> },
  { path: "/shipping", element: <ShippingPage /> },
  { path: "/coa", element: <COAPage /> },
  { path: "/analysis/ml", element: <DailyMLPage /> },
  { path: "/analysis/msl", element: <DailyMSLPage /> },
  { path: "/analysis/attribute", element: <DailyAttributePage /> },
  { path: "/risk", element: <RiskPage /> },
  { path: "/data-management", element: <DataManagementPage /> },
  { path: "/admin/users", element: <UsersPage /> },
  { path: "/login", element: <LoginPage /> },
];
```

- [ ] **Step 7: Verify frontend starts**

```bash
cd frontend
npm run dev
# Visit http://localhost:8080 → see layout with sidebar
```

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend with React + Vite + TailwindCSS + routing"
```

---

### Task 6: Frontend Authentication (Azure AD SSO)

**Files:**
- Create: `frontend/src/features/auth/LoginPage.tsx`
- Create: `frontend/src/features/auth/AuthProvider.tsx`
- Create: `frontend/src/features/auth/useAuth.ts`
- Create: `frontend/src/lib/msal-config.ts`

- [ ] **Step 1: Configure MSAL**

Same pattern as Dt_Quality_Roadmap — configure Azure AD client ID, redirect URI, scopes.

- [ ] **Step 2: Create AuthProvider context**

Manages: access_token, user info, login/logout, token refresh.

- [ ] **Step 3: Create LoginPage**

"Login with Corning SSO" button → acquires Azure AD token → calls backend `/api/v1/auth/sso-login`.

- [ ] **Step 4: Add route guards**

Protected routes redirect to `/login` if no valid token.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend auth (Azure AD SSO + JWT)"
```

---

## Phase 2: ETL Layer

### Task 7: ETL Scheduler Setup (APScheduler)

**Files:**
- Create: `backend/app/etl/scheduler.py`
- Modify: `backend/app/main.py` (add scheduler startup)

- [ ] **Step 1: Create scheduler**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

scheduler = AsyncIOScheduler()


def setup_scheduler():
    if not settings.etl_enabled:
        return

    from app.etl.batch_sync import run_batch_sync
    from app.etl.defect_sync import run_defect_sync
    from app.etl.cube_sync import run_cube_sync
    from app.etl.shipping_import import run_shipping_import

    scheduler.add_job(run_batch_sync, CronTrigger(hour=6, minute=0), id="batch_sync")
    scheduler.add_job(run_defect_sync, CronTrigger(hour=6, minute=15), id="defect_sync")
    scheduler.add_job(run_cube_sync, CronTrigger(hour=6, minute=30), id="cube_sync")
    scheduler.add_job(run_shipping_import, CronTrigger(hour=6, minute=45), id="shipping_import")

    scheduler.start()
```

- [ ] **Step 2: Wire scheduler into FastAPI startup**

Add to `main.py`:
```python
@app.on_event("startup")
async def startup_event():
    from app.etl.scheduler import setup_scheduler
    setup_scheduler()
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/etl/ backend/app/main.py
git commit -m "feat: add APScheduler with daily ETL job schedule"
```

---

### Task 8: Batch & Defect ETL (Oracle + MSSQL)

**Files:**
- Create: `backend/app/etl/batch_sync.py`
- Create: `backend/app/etl/defect_sync.py`
- Create: `backend/app/etl/connections.py`

- [ ] **Step 1: Create external DB connection helpers**

Reuse logic from existing `utils/db_connections.py` — wrap into `backend/app/etl/connections.py`.

- [ ] **Step 2: Implement batch_sync**

Queries MESDW for recent batches → upserts into PostgreSQL `batches` table. Logs to `etl_jobs`.

- [ ] **Step 3: Implement defect_sync**

Loops through new batch_ids → queries Oracle PPDA → inserts into `defects` table. Logs to `etl_jobs`.

- [ ] **Step 4: Test with mock data and commit**

```bash
pytest tests/test_etl_batch.py -v
git add backend/
git commit -m "feat: add batch + defect ETL sync from Oracle/MSSQL"
```

---

### Task 9: Cube MSL ETL

**Files:**
- Create: `backend/app/etl/cube_sync.py`

- [ ] **Step 1: Implement cube_sync**

Reuse MDX query from existing `utils/sql_queries.py`. Fetches cube data → pivots → writes to `cube_msl` table.

- [ ] **Step 2: Commit**

```bash
git add backend/app/etl/cube_sync.py
git commit -m "feat: add SSAS Cube MSL ETL sync"
```

---

### Task 10: Shipping Excel Import ETL

**Files:**
- Create: `backend/app/etl/shipping_import.py`

- [ ] **Step 1: Implement shipping_import**

- Scan shared folder for new Excel files (by modified date)
- Parse Excel columns: plant, target_qty, ship_date
- Upsert into `shipping_schedules` table
- Log to `etl_jobs`

- [ ] **Step 2: Commit**

```bash
git add backend/app/etl/shipping_import.py
git commit -m "feat: add shipping schedule Excel import ETL"
```

---

## Phase 3: Core Features

### Task 11: PCI Offload — Backend API

**Files:**
- Create: `backend/app/routers/offload.py`
- Create: `backend/app/services/offload_service.py`
- Create: `backend/app/schemas/offload.py`

- [ ] **Step 1: Create offload service**

Business logic:
- Given plant_id → fetch criteria
- Query available crates from `batches` + compute defect ratios from `defects`
- Evaluate each crate against criteria → mark pass/fail
- Return list with compliance status

- [ ] **Step 2: Create API endpoints**

- `GET /api/v1/offload/plants` — list active plants
- `GET /api/v1/offload/crates?plant_id=X` — get evaluated crate list
- `POST /api/v1/offload/select` — confirm crate selection (body: crate_ids, plant_id)
  - Check permission for non-compliant crates (`offload_override`)
- `GET /api/v1/offload/selections` — get current selections

- [ ] **Step 3: Test and commit**

```bash
pytest tests/test_offload.py -v
git add backend/
git commit -m "feat: add PCI Offload backend API"
```

---

### Task 12: PCI Offload — Frontend

**Files:**
- Create: `frontend/src/features/offload/OffloadPage.tsx`
- Create: `frontend/src/features/offload/CrateTable.tsx`
- Create: `frontend/src/features/offload/CriteriaPanel.tsx`

- [ ] **Step 1: Build plant selector + criteria panel**
- [ ] **Step 2: Build crate table with TanStack Table**

Columns: checkbox, crate_id, Gen, defect ratios (colored), in_qty.
Lock icon on non-compliant rows for unauthorized users.

- [ ] **Step 3: Add confirm offload action**
- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/offload/
git commit -m "feat: add PCI Offload frontend (plant selector + crate table)"
```

---

### Task 13: Shipping Assumption — Backend API

**Files:**
- Create: `backend/app/routers/shipping.py`
- Create: `backend/app/services/shipping_service.py`
- Create: `backend/app/schemas/shipping.py`

- [ ] **Step 1: Implement FIFO assignment service**

Logic:
1. For each schedule (ship_date, plant_id, target_qty):
2. Query pool: `batches WHERE cut_lot_end_date <= (ship_date - 3) AND crate meets criteria AND not assigned`
3. Sort by cut_lot_end_date ASC, crate_id ASC
4. Accumulate in_qty until target reached
5. Write assignments to `shipping_assignments`
6. Surplus → mark for risk management

- [ ] **Step 2: Create API endpoints**

- `GET /api/v1/shipping/schedules` — list schedules with assignment status
- `GET /api/v1/shipping/schedules/{id}/assignments` — FIFO-assigned crates
- `POST /api/v1/shipping/recalculate` — re-run FIFO assignment

- [ ] **Step 3: Commit**

```bash
git add backend/
git commit -m "feat: add Shipping Assumption backend with FIFO logic"
```

---

### Task 14: Shipping Assumption — Frontend

**Files:**
- Create: `frontend/src/features/shipping/ShippingPage.tsx`
- Create: `frontend/src/features/shipping/ScheduleTable.tsx`
- Create: `frontend/src/features/shipping/AssignmentDetail.tsx`

- [ ] **Step 1: Build schedule summary table**
- [ ] **Step 2: Add expandable rows with assigned crate details**
- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/shipping/
git commit -m "feat: add Shipping Assumption frontend"
```

---

### Task 15: COA — Backend + Frontend

**Files:**
- Create: `backend/app/routers/coa.py`
- Create: `backend/app/services/coa_service.py`
- Create: `frontend/src/features/coa/COAPage.tsx`

- [ ] **Step 1: Backend — COA data endpoint**

- `GET /api/v1/coa/data` — returns full defect ratio + MSL for selected offload crates
- `GET /api/v1/coa/export` — returns Excel file (openpyxl generated)

- [ ] **Step 2: Frontend — COA table + export button**
- [ ] **Step 3: Commit**

```bash
git add backend/ frontend/src/features/coa/
git commit -m "feat: add COA tab (data table + Excel export)"
```

---

### Task 16: Integration test — Offload → Shipping → COA flow

**Files:**
- Create: `backend/tests/test_integration_flow.py`

- [ ] **Step 1: Write end-to-end flow test**

Seed data → run offload selection → verify shipping assignment → verify COA output.

- [ ] **Step 2: Commit**

```bash
git add backend/tests/
git commit -m "test: add integration test for Offload → Shipping → COA flow"
```

---

## Phase 4: Analysis Dashboards

### Task 17: Daily Analysis API (shared endpoint)

**Files:**
- Create: `backend/app/routers/analysis.py`
- Create: `backend/app/schemas/analysis.py`

- [ ] **Step 1: Create analysis endpoints**

- `GET /api/v1/analysis/ml?item=Blister` — returns {tank_id, date, crate_id, value}[]
- `GET /api/v1/analysis/msl?item=Cord` — same structure
- `GET /api/v1/analysis/attribute?item=MAX_THICKNESS` — same structure
- `GET /api/v1/analysis/items/{type}` — returns available items for dropdown (ml/msl/attribute)
- `GET /api/v1/analysis/tanks` — returns active tanks

- [ ] **Step 2: Commit**

```bash
git add backend/app/routers/analysis.py backend/app/schemas/analysis.py
git commit -m "feat: add Daily Analysis API endpoints"
```

---

### Task 18: Stacked Chart Component

**Files:**
- Create: `frontend/src/components/charts/StackedBarChart.tsx`
- Create: `frontend/src/features/daily-analysis/TankChartGrid.tsx`

- [ ] **Step 1: Create reusable ECharts stacked bar component**

Props: `{ title, xData: string[], series: {name: string, data: number[]}[] }`

- [ ] **Step 2: Create TankChartGrid**

Fetches all tanks, renders one StackedBarChart per tank in a responsive grid.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/charts/ frontend/src/features/daily-analysis/
git commit -m "feat: add reusable stacked bar chart + tank grid component"
```

---

### Task 19: Daily Analysis Pages (ML, MSL, Attribute)

**Files:**
- Create: `frontend/src/features/daily-analysis/DailyMLPage.tsx`
- Create: `frontend/src/features/daily-analysis/DailyMSLPage.tsx`
- Create: `frontend/src/features/daily-analysis/DailyAttributePage.tsx`

- [ ] **Step 1: Create ML page with item dropdown + chart grid**
- [ ] **Step 2: Create MSL page (same pattern)**
- [ ] **Step 3: Create Attribute page (same pattern)**
- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/daily-analysis/
git commit -m "feat: add Daily Analysis pages (ML, MSL, Attribute)"
```

---

## Phase 5: Risk & Data Management

### Task 20: Risk Management — Backend + Frontend

**Files:**
- Create: `backend/app/routers/risk.py`
- Create: `backend/app/services/risk_service.py`
- Create: `frontend/src/features/risk/RiskPage.tsx`

- [ ] **Step 1: Backend — risk crate listing**

- `GET /api/v1/risk/crates?level=all` — returns crates with risk assessment
- Sources: failed criteria crates + surplus shipping crates
- `GET /api/v1/risk/rules` — list active rules
- `POST /api/v1/risk/rules` — create rule (requires `risk_mgmt`)

- [ ] **Step 2: Frontend — risk table with level filter + color coding**
- [ ] **Step 3: Commit**

```bash
git add backend/ frontend/src/features/risk/
git commit -m "feat: add Risk Management tab"
```

---

### Task 21: Data Management — Backend + Frontend

**Files:**
- Create: `backend/app/routers/data_management.py`
- Create: `frontend/src/features/data-mgmt/DataManagementPage.tsx`
- Create: `frontend/src/features/data-mgmt/CrudTable.tsx`

- [ ] **Step 1: Backend — generic CRUD endpoints**

- `GET/POST/PUT/DELETE /api/v1/data-mgmt/plants`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/plant-criteria`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/tanks`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/ml-items`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/msl-items`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/attribute-items`
- `GET/POST/PUT/DELETE /api/v1/data-mgmt/risk-rules`

All require `data_mgmt` permission.

- [ ] **Step 2: Frontend — sub-tab navigation + reusable CrudTable**
- [ ] **Step 3: Commit**

```bash
git add backend/ frontend/src/features/data-mgmt/
git commit -m "feat: add Data Management tab (CRUD for all config entities)"
```

---

### Task 22: Admin Dashboard + ETL Status

**Files:**
- Create: `backend/app/routers/admin.py`
- Create: `frontend/src/features/admin/AdminPage.tsx`

- [ ] **Step 1: Backend — ETL status endpoint**

- `GET /api/v1/admin/etl-status` — recent ETL jobs with status
- `POST /api/v1/admin/etl/trigger/{job_type}` — manually trigger ETL job

- [ ] **Step 2: Frontend — ETL status panel + user management**
- [ ] **Step 3: Final commit**

```bash
git add backend/ frontend/
git commit -m "feat: add Admin dashboard with ETL status + user management"
```

---

## Final Steps

- [ ] **Seed data script**: Create `backend/app/seed.py` to populate initial plants, tanks, ML/MSL/Attribute items
- [ ] **README update**: Document setup steps (PostgreSQL install, `.env` config, run commands)
- [ ] **Push to GitHub**

```bash
git push origin main
```
