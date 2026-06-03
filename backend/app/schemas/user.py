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
    role: str


class UpdateUserStatus(BaseModel):
    status: str


class UpdateUserPermissions(BaseModel):
    permissions: list[str]
