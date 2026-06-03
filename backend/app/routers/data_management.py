from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_permission
from app.models.data_management import AttributeItem, MlItem, MslItem, Tank
from app.models.plant import Plant, PlantCriteria
from app.models.user import User
from app.schemas.common import ok

router = APIRouter(prefix="/api/v1/data-mgmt", tags=["data-management"])


# --- Schemas ---


class PlantCreate(BaseModel):
    name: str
    code: str
    is_active: bool = True


class PlantUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    is_active: bool | None = None


class CriteriaCreate(BaseModel):
    plant_id: int
    defect_type: str
    min_size: float | None = None
    operator: str = "<"
    threshold: float
    is_active: bool = True


class CriteriaUpdate(BaseModel):
    defect_type: str | None = None
    min_size: float | None = None
    operator: str | None = None
    threshold: float | None = None
    is_active: bool | None = None


class TankCreate(BaseModel):
    name: str
    code: str
    is_active: bool = True
    sort_order: int = 0


class TankUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class ItemCreate(BaseModel):
    name: str
    display_name: str | None = None
    is_active: bool = True
    sort_order: int = 0


class ItemUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


# --- Plants ---


@router.get("/plants")
def list_plants(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    items = db.query(Plant).all()
    return ok([
        {"id": i.id, "name": i.name, "code": i.code, "is_active": i.is_active}
        for i in items
    ])


@router.post("/plants")
def create_plant(
    body: PlantCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = Plant(name=body.name, code=body.code, is_active=body.is_active)
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/plants/{item_id}")
def update_plant(
    item_id: int,
    body: PlantUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(Plant).filter(Plant.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/plants/{item_id}")
def delete_plant(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(Plant).filter(Plant.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})


# --- Plant Criteria ---


@router.get("/plant-criteria")
def list_criteria(
    plant_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    query = db.query(PlantCriteria)
    if plant_id:
        query = query.filter(PlantCriteria.plant_id == plant_id)
    items = query.all()
    return ok([
        {
            "id": i.id,
            "plant_id": i.plant_id,
            "defect_type": i.defect_type,
            "min_size": i.min_size,
            "operator": i.operator,
            "threshold": i.threshold,
            "is_active": i.is_active,
        }
        for i in items
    ])


@router.post("/plant-criteria")
def create_criteria(
    body: CriteriaCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = PlantCriteria(
        plant_id=body.plant_id,
        defect_type=body.defect_type,
        min_size=body.min_size,
        operator=body.operator,
        threshold=body.threshold,
        is_active=body.is_active,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/plant-criteria/{item_id}")
def update_criteria(
    item_id: int,
    body: CriteriaUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(PlantCriteria).filter(PlantCriteria.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/plant-criteria/{item_id}")
def delete_criteria(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(PlantCriteria).filter(PlantCriteria.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})


# --- Tanks ---


@router.get("/tanks")
def list_tanks(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    items = db.query(Tank).order_by(Tank.sort_order).all()
    return ok([
        {
            "id": i.id,
            "name": i.name,
            "code": i.code,
            "is_active": i.is_active,
            "sort_order": i.sort_order,
        }
        for i in items
    ])


@router.post("/tanks")
def create_tank(
    body: TankCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = Tank(
        name=body.name, code=body.code, is_active=body.is_active, sort_order=body.sort_order
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/tanks/{item_id}")
def update_tank(
    item_id: int,
    body: TankUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(Tank).filter(Tank.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/tanks/{item_id}")
def delete_tank(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(Tank).filter(Tank.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})


# --- ML Items ---


@router.get("/ml-items")
def list_ml_items(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    items = db.query(MlItem).order_by(MlItem.sort_order).all()
    return ok([
        {
            "id": i.id,
            "name": i.name,
            "display_name": i.display_name,
            "is_active": i.is_active,
            "sort_order": i.sort_order,
        }
        for i in items
    ])


@router.post("/ml-items")
def create_ml_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = MlItem(
        name=body.name,
        display_name=body.display_name,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/ml-items/{item_id}")
def update_ml_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(MlItem).filter(MlItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/ml-items/{item_id}")
def delete_ml_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(MlItem).filter(MlItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})


# --- MSL Items ---


@router.get("/msl-items")
def list_msl_items(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    items = db.query(MslItem).order_by(MslItem.sort_order).all()
    return ok([
        {
            "id": i.id,
            "name": i.name,
            "display_name": i.display_name,
            "is_active": i.is_active,
            "sort_order": i.sort_order,
        }
        for i in items
    ])


@router.post("/msl-items")
def create_msl_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = MslItem(
        name=body.name,
        display_name=body.display_name,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/msl-items/{item_id}")
def update_msl_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(MslItem).filter(MslItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/msl-items/{item_id}")
def delete_msl_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(MslItem).filter(MslItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})


# --- Attribute Items ---


@router.get("/attribute-items")
def list_attribute_items(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    items = db.query(AttributeItem).order_by(AttributeItem.sort_order).all()
    return ok([
        {
            "id": i.id,
            "name": i.name,
            "display_name": i.display_name,
            "is_active": i.is_active,
            "sort_order": i.sort_order,
        }
        for i in items
    ])


@router.post("/attribute-items")
def create_attribute_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = AttributeItem(
        name=body.name,
        display_name=body.display_name,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return ok({"id": item.id})


@router.put("/attribute-items/{item_id}")
def update_attribute_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(AttributeItem).filter(AttributeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, val in body.model_dump(exclude_none=True).items():
        setattr(item, key, val)
    db.commit()
    return ok({"message": "Updated"})


@router.delete("/attribute-items/{item_id}")
def delete_attribute_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("data_mgmt")),
):
    item = db.query(AttributeItem).filter(AttributeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(item)
    db.commit()
    return ok({"message": "Deleted"})
