import hashlib
import os
import secrets
from datetime import datetime

from backend.database import SystemSettings, User, UserSession, get_session
from backend.schemas import LoginRequest, RegisterRequest
from fastapi import APIRouter, HTTPException
from sqlmodel import select

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
def register(req: RegisterRequest):
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if settings and not settings.registration_open:
            raise HTTPException(status_code=403, detail="Registration is currently closed.")

        existing = session.exec(select(User).where(User.username == req.username)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")

        user = User(
            username=req.username,
            password_hash=hash_password(req.password),
            created_at=datetime.utcnow().isoformat() + "Z",
            is_admin=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = secrets.token_hex(32)
        user_session = UserSession(token=token, user_id=user.id, created_at=datetime.utcnow().isoformat() + "Z")
        session.add(user_session)
        session.commit()

        return {"status": "success", "token": token, "user_id": user.id}

@router.post("/login")
def login(req: LoginRequest):
    with get_session() as session:
        admin_secret_env = os.environ.get("SAOS_ADMIN_SECRET", "admin")
        if req.username == "admin" and admin_secret_env and req.password == admin_secret_env:
            user = session.exec(select(User).where(User.username == "admin")).first()
            if not user:
                user = User(
                    username="admin",
                    password_hash=hash_password(req.password),
                    created_at=datetime.utcnow().isoformat() + "Z",
                    is_admin=True,
                )
                session.add(user)
                session.commit()
                session.refresh(user)
        else:
            user = session.exec(select(User).where(User.username == req.username)).first()
            if not user or user.password_hash != hash_password(req.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")

        token = secrets.token_hex(32)
        user_session = UserSession(token=token, user_id=user.id, created_at=datetime.utcnow().isoformat() + "Z")
        session.add(user_session)
        session.commit()

        return {"status": "success", "token": token, "user_id": user.id, "is_admin": user.is_admin}
