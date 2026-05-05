from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.services.auth_service import create_jwt, decode_jwt, hash_password, verify_password

router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    name: str
    plan: str


@router.post("/register", response_model=AuthOut)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    exists = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "email already registered")
    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        plan="free",
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()
    token = create_jwt({"uid": user.id, "email": user.email, "plan": user.plan})
    await db.commit()
    return AuthOut(access_token=token, user_id=user.id, email=user.email, name=user.name, plan=user.plan)


@router.post("/login", response_model=AuthOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    token = create_jwt({"uid": user.id, "email": user.email, "plan": user.plan})
    return AuthOut(access_token=token, user_id=user.id, email=user.email, name=user.name, plan=user.plan)


async def current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(401, "invalid or expired token")
    user = (await db.execute(select(User).where(User.id == payload["uid"]))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "user not found or inactive")
    return user


@router.get("/me", response_model=AuthOut)
async def me(user: User = Depends(current_user)):
    return AuthOut(
        access_token="",
        user_id=user.id,
        email=user.email,
        name=user.name,
        plan=user.plan,
    )
