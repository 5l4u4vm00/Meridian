from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    name: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: str | None = None
    permissions: list[str] = []

    @classmethod
    def from_user(cls, user) -> "UserRead":
        role_name = user.role.name if user.role is not None else None
        perms = [p.name for p in user.role.permissions] if user.role is not None else []
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            role=role_name,
            permissions=perms,
        )


class RoleAssign(BaseModel):
    role: str
