from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.daily_analysis import DailyAttribute, DailyMl, DailyMsl
from app.models.data_management import AttributeItem, MlItem, MslItem, Tank
from app.models.user import User
from app.schemas.analysis import AnalysisDataPoint, ItemInfo, TankInfo
from app.schemas.common import ok

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.get("/tanks")
def list_tanks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    tanks = db.query(Tank).filter(Tank.is_active == True).order_by(Tank.sort_order).all()
    return ok([TankInfo(id=t.id, name=t.name, code=t.code).model_dump() for t in tanks])


@router.get("/items/{analysis_type}")
def list_items(
    analysis_type: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List available items for dropdown. analysis_type: ml, msl, or attribute"""
    if analysis_type == "ml":
        items = db.query(MlItem).filter(MlItem.is_active == True).order_by(MlItem.sort_order).all()
    elif analysis_type == "msl":
        items = db.query(MslItem).filter(MslItem.is_active == True).order_by(MslItem.sort_order).all()
    elif analysis_type == "attribute":
        items = db.query(AttributeItem).filter(AttributeItem.is_active == True).order_by(AttributeItem.sort_order).all()
    else:
        return ok([])

    return ok([ItemInfo(id=i.id, name=i.name, display_name=i.display_name).model_dump() for i in items])


@router.get("/ml")
def get_ml_data(
    item: str,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMl)
        .filter(DailyMl.item_name == item, DailyMl.date >= since)
        .order_by(DailyMl.tank_id, DailyMl.date)
        .all()
    )
    tanks = {t.id: t.name for t in db.query(Tank).all()}
    return ok([
        AnalysisDataPoint(
            tank_id=r.tank_id,
            tank_name=tanks.get(r.tank_id),
            crate_id=r.crate_id,
            date=r.date,
            value=r.value,
        ).model_dump()
        for r in rows
    ])


@router.get("/msl")
def get_msl_data(
    item: str,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyMsl)
        .filter(DailyMsl.item_name == item, DailyMsl.date >= since)
        .order_by(DailyMsl.tank_id, DailyMsl.date)
        .all()
    )
    tanks = {t.id: t.name for t in db.query(Tank).all()}
    return ok([
        AnalysisDataPoint(
            tank_id=r.tank_id,
            tank_name=tanks.get(r.tank_id),
            crate_id=r.crate_id,
            date=r.date,
            value=r.value,
        ).model_dump()
        for r in rows
    ])


@router.get("/attribute")
def get_attribute_data(
    item: str,
    days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=days)
    rows = (
        db.query(DailyAttribute)
        .filter(DailyAttribute.item_name == item, DailyAttribute.date >= since)
        .order_by(DailyAttribute.tank_id, DailyAttribute.date)
        .all()
    )
    tanks = {t.id: t.name for t in db.query(Tank).all()}
    return ok([
        AnalysisDataPoint(
            tank_id=r.tank_id,
            tank_name=tanks.get(r.tank_id),
            crate_id=r.crate_id,
            date=r.date,
            value=r.value,
        ).model_dump()
        for r in rows
    ])
