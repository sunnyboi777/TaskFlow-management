from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    email: str = Field(
        min_length=5,
        max_length=255,
    )
    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLogin(BaseModel):
    email: str = Field(
        min_length=5,
        max_length=255,
    )
    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut