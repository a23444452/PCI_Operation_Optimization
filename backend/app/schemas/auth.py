from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class SSOLoginRequest(BaseModel):
    access_token: str


class SSORegisterRequest(BaseModel):
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


class SSOLoginNeedRegistration(BaseModel):
    status: str = "need_registration"
    username: str
    email: str
    display_name: str


class SSOLoginPendingApproval(BaseModel):
    status: str = "pending_approval"
    username: str


class SSOLoginAuthenticated(BaseModel):
    status: str = "authenticated"
    access_token: str
    expires_in: int
    user: UserInfo
