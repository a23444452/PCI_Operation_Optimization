from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_permission
from app.models.risk import RiskAssessment, RiskRule
from app.models.user import User
from app.schemas.common import ok

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


class RiskRuleCreate(BaseModel):
    name: str
    conditions_json: dict
    risk_level: str


@router.get("/crates")
def list_risk_crates(
    level: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List crates with risk assessments."""
    query = db.query(RiskAssessment)
    if level and level != "all":
        query = query.filter(RiskAssessment.risk_level == level)
    assessments = query.order_by(RiskAssessment.assessed_at.desc()).all()
    return ok([
        {
            "id": a.id,
            "crate_id": a.crate_id,
            "risk_level": a.risk_level,
            "rule_id": a.rule_id,
            "assessed_at": a.assessed_at.isoformat() if a.assessed_at else None,
            "reason": a.reason,
        }
        for a in assessments
    ])


@router.get("/rules")
def list_rules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rules = db.query(RiskRule).filter(RiskRule.is_active == True).all()
    return ok([
        {
            "id": r.id,
            "name": r.name,
            "conditions_json": r.conditions_json,
            "risk_level": r.risk_level,
            "is_active": r.is_active,
        }
        for r in rules
    ])


@router.post("/rules")
def create_rule(
    body: RiskRuleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission("risk_mgmt")),
):
    rule = RiskRule(
        name=body.name,
        conditions_json=body.conditions_json,
        risk_level=body.risk_level,
        is_active=True,
        created_by=user.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return ok({"id": rule.id, "message": "Rule created"})
