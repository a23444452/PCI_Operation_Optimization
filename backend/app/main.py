from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.middleware.rate_limit import limiter


@asynccontextmanager
async def lifespan(app):
    from app.etl.scheduler import setup_scheduler

    setup_scheduler()
    yield


app = FastAPI(title="PCI Operation Optimization", version="0.1.0", lifespan=lifespan)

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


from app.routers.auth import router as auth_router

app.include_router(auth_router)

from app.routers.users import router as users_router

app.include_router(users_router)

from app.routers.offload import router as offload_router

app.include_router(offload_router)

from app.routers.shipping import router as shipping_router

app.include_router(shipping_router)

from app.routers.coa import router as coa_router

app.include_router(coa_router)

from app.routers.analysis import router as analysis_router

app.include_router(analysis_router)

from app.routers.risk import router as risk_router

app.include_router(risk_router)

from app.routers.data_management import router as data_mgmt_router

app.include_router(data_mgmt_router)

from app.routers.admin import router as admin_router

app.include_router(admin_router)
