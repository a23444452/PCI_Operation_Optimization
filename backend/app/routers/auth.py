from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    SSOLoginAuthenticated,
    SSOLoginNeedRegistration,
    SSOLoginPendingApproval,
    SSOLoginRequest,
    SSORegisterRequest,
    UserInfo,
)
from app.schemas.common import ok
from app.services.auth_service import _unusable_password_hash, authenticate_user
from app.utils.azure_ad import AzureADTokenError, verify_azure_access_token
from app.utils.email import send_new_user_registration_notification, send_user_pending_notification
from app.utils.ldap_validation import check_ad_group_membership
from app.utils.security import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _build_user_info(user: User) -> UserInfo:
    return UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        role=user.role,
        permissions=[p.feature_key for p in user.permissions],
    )


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.jwt_refresh_expiry_days * 86400,
    )

    return ok(
        LoginResponse(
            access_token=access_token,
            expires_in=settings.jwt_expiry_hours * 3600,
            user=_build_user_info(user),
        ).model_dump()
    )


@router.post("/sso-login")
@limiter.limit("10/minute")
def sso_login(
    request: Request,
    response: Response,
    body: SSOLoginRequest,
    db: Session = Depends(get_db),
):
    # Verify Azure AD token
    try:
        claims = verify_azure_access_token(body.access_token)
    except AzureADTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    upn = claims["upn"]
    username = upn.split("@")[0].lower()

    # Check AD group membership
    if not check_ad_group_membership(username, settings.ad_required_group):
        raise HTTPException(
            status_code=403,
            detail=f"Not a member of required AD group: {settings.ad_required_group}",
        )

    # Look up user in local database
    user = db.query(User).filter(func.lower(User.username) == username).first()

    if user is None:
        display_name = claims.get("name", username)
        email = claims.get("upn", f"{username}@corning.com")
        return ok(
            SSOLoginNeedRegistration(
                username=username,
                email=email,
                display_name=display_name,
            ).model_dump()
        )

    if user.status == "pending":
        return ok(SSOLoginPendingApproval(username=username).model_dump())

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Account is not active")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.jwt_refresh_expiry_days * 86400,
    )

    return ok(
        SSOLoginAuthenticated(
            access_token=access_token,
            expires_in=settings.jwt_expiry_hours * 3600,
            user=_build_user_info(user),
        ).model_dump()
    )


@router.post("/sso-register")
@limiter.limit("3/minute")
def sso_register(
    request: Request,
    body: SSORegisterRequest,
    db: Session = Depends(get_db),
):
    # Verify Azure AD token
    try:
        claims = verify_azure_access_token(body.access_token)
    except AzureADTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    upn = claims["upn"]
    username = upn.split("@")[0].lower()

    # Check AD group membership
    if not check_ad_group_membership(username, settings.ad_required_group):
        raise HTTPException(
            status_code=403,
            detail=f"Not a member of required AD group: {settings.ad_required_group}",
        )

    # Check if user already exists
    existing = db.query(User).filter(func.lower(User.username) == username).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="User already registered")

    # Create user with pending status
    display_name = claims.get("name", username)
    email = claims.get("upn", f"{username}@corning.com")

    new_user = User(
        username=username,
        email=email,
        password_hash=_unusable_password_hash(),
        display_name=display_name,
        role="viewer",
        status="pending",
    )
    db.add(new_user)
    db.commit()

    # Notify admins via email
    if settings.admin_notification_emails:
        admin_emails = [e.strip() for e in settings.admin_notification_emails.split(",") if e.strip()]
    else:
        admin_emails = [
            u.email
            for u in db.query(User).filter(User.role == "admin", User.status == "active").all()
            if u.email
        ]
    if admin_emails:
        send_new_user_registration_notification(
            admin_emails=admin_emails,
            username=username,
            display_name=display_name,
            email=email,
        )

    # Notify user that registration is pending
    send_user_pending_notification(
        user_email=email,
        username=username,
        display_name=display_name,
    )

    return ok({"message": "Registration submitted. Awaiting admin approval."})


@router.post("/refresh")
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access_token = create_access_token(user.id, user.role)

    return ok({"access_token": access_token, "expires_in": settings.jwt_expiry_hours * 3600})


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return ok(
        UserInfo(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            role=user.role,
            permissions=[p.feature_key for p in user.permissions],
        ).model_dump()
    )


@router.get("/system-config")
def system_config():
    admin_emails = []
    if settings.admin_notification_emails:
        admin_emails = [e.strip() for e in settings.admin_notification_emails.split(",") if e.strip()]
    return ok({
        "admin_emails": admin_emails,
        "app_url": settings.app_base_url,
    })
