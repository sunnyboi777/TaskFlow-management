
import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from ... import models
from ...schemas.auth import (
    UserRegister,
    UserLogin,
    UserOut,
    TokenResponse,
)


router = APIRouter(prefix="/auth", tags=["Authentication"])

bearer_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    email = user_data.email.strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter a valid email address.",
        )

    existing_user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = models.User(
        email=email,
        hashed_password=hash_password(user_data.password),
        role="user",
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    email = user_data.email.strip().lower()

    user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if (
        user is None
        or not verify_password(
            user_data.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = decode_access_token(credentials.credentials)

    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(models.User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive.",
        )

    return user


# ADMIN AUTHORIZATION
def require_admin(
    current_user=Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user
