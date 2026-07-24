from datetime import datetime
from typing import Optional

from backend.client import VLLMClient
from backend.database import NPC as DBNPC
from backend.database import BugReport, LedgerEntry, SystemSettings, User, UserSession, get_session
from backend.routers.auth import hash_password
from backend.schemas import BugReportRequest, NPCUpdate, RegisterRequest, SettingsUpdate
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import select

router = APIRouter()

def get_admin_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split("Bearer ")[1]
    with get_session() as session:
        user_session = session.exec(select(UserSession).where(UserSession.token == token)).first()
        if not user_session:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = session.get(User, user_session.user_id)
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return user

@router.get("/settings")
def get_settings(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if not settings:
            settings = SystemSettings()
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return {"registration_open": settings.registration_open, "global_system_prompt": settings.global_system_prompt}

@router.post("/settings")
def update_settings(req: SettingsUpdate, admin: User = Depends(get_admin_user)):
    with get_session() as session:
        settings = session.exec(select(SystemSettings)).first()
        if not settings:
            settings = SystemSettings()
            session.add(settings)
        settings.registration_open = req.registration_open
        if req.global_system_prompt is not None:
            settings.global_system_prompt = req.global_system_prompt
        session.commit()
        return {"status": "success"}

@router.get("/users")
def get_users(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        users = session.exec(select(User)).all()
        return {"users": [{"id": u.id, "username": u.username, "is_admin": u.is_admin} for u in users]}

@router.get("/npcs")
def get_npcs(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        npcs = session.exec(select(DBNPC)).all()
        return {"npcs": [{"id": n.id, "name": n.name, "custom_system_prompt": n.custom_system_prompt} for n in npcs]}

@router.put("/npcs/{npc_id}")
def update_npc(npc_id: str, req: NPCUpdate, admin: User = Depends(get_admin_user)):
    with get_session() as session:
        npc = session.get(DBNPC, npc_id)
        if not npc:
            raise HTTPException(status_code=404, detail="NPC not found")
        npc.custom_system_prompt = req.custom_system_prompt
        session.commit()
        return {"status": "success"}

@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(get_admin_user)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        session.delete(user)
        session.commit()
        return {"status": "success"}

@router.post("/reset-password/{user_id}")
def reset_password(user_id: int, req: RegisterRequest, admin: User = Depends(get_admin_user)):
    with get_session() as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.password_hash = hash_password(req.password)
        session.add(user)
        session.commit()
        return {"status": "success"}

@router.get("/logs")
def get_logs(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        entries = session.exec(select(LedgerEntry).order_by(LedgerEntry.timestamp.desc()).limit(50)).all()
        return {
            "logs": [
                {
                    "id": e.id,
                    "character_id": e.character_id,
                    "action": e.action,
                    "narration": e.narration,
                    "timestamp": e.timestamp,
                }
                for e in entries
            ]
        }

@router.post("/bugreports")
def submit_bugreport(req: BugReportRequest):
    with get_session() as session:
        bug = BugReport(
            user_id=req.user_id, type=req.type, original_text=req.text, created_at=datetime.utcnow().isoformat() + "Z"
        )
        session.add(bug)
        session.commit()
        session.refresh(bug)
        return {"status": "success", "bug_id": bug.id}

@router.get("/bugreports")
def get_bugreports(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.desc())).all()
        return {
            "bugreports": [
                {
                    "id": b.id,
                    "user_id": b.user_id,
                    "type": b.type,
                    "original_text": b.original_text,
                    "optimized_text": b.optimized_text,
                    "status": b.status,
                    "created_at": b.created_at,
                }
                for b in bugs
            ]
        }

@router.delete("/bugreports/{bug_id}")
def delete_bugreport(bug_id: int, admin: User = Depends(get_admin_user)):
    with get_session() as session:
        bug = session.get(BugReport, bug_id)
        if not bug:
            raise HTTPException(status_code=404, detail="Bug report not found")
        session.delete(bug)
        session.commit()
        return {"status": "success"}

@router.post("/reports/export_roadmap")
def export_roadmap(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.desc())).all()

        if not bugs:
            return {"roadmap": "No reports found to generate roadmap."}

        prompt = "You are a product manager and lead engineer. Below are the community reports (bugs and feature requests). Please analyze all of them, order them by logical priority (critical bugs first, then important features, etc.), and create a clear, step-by-step technical roadmap for development.\n\n"
        for b in bugs:
            prompt += f"[{b.type.upper()}] Report {b.id}:\n{b.original_text}\n\n"

        prompt += "Roadmap:\n"

        try:
            client = VLLMClient()
            response = client.generate(prompt=prompt, max_tokens=1000, temperature=0.7)
            roadmap_text = ""
            if isinstance(response, dict) and "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "text" in choice:
                    roadmap_text = choice["text"]
                elif "message" in choice:
                    roadmap_text = choice["message"].get("content", "")
            elif isinstance(response, dict) and "text" in response:
                roadmap_text = response["text"]
            elif isinstance(response, str):
                roadmap_text = response

            return {"roadmap": roadmap_text.strip()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"VLLM processing failed: {str(e)}")

@router.get("/reports/fetch_and_clear")
def fetch_and_clear(admin: User = Depends(get_admin_user)):
    with get_session() as session:
        bugs = session.exec(select(BugReport).order_by(BugReport.id.asc())).all()
        data = []
        for b in bugs:
            data.append({"id": b.id, "type": b.type, "text": b.original_text, "created_at": b.created_at})
            session.delete(b)
        session.commit()
        return {"reports": data}
