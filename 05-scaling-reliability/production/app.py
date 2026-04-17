import os
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import redis
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel, Field

# --- Cấu hình ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
INSTANCE_ID = f"agent-{uuid.uuid4().hex[:6]}"

# --- Models ---
class Message(BaseModel):
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

# --- Stateless Storage Manager ---
class SessionStore:
    """Quản lý State tập trung tại Redis"""
    def __init__(self, redis_url: str):
        try:
            self.client = redis.from_url(redis_url, decode_responses=True)
            self.client.ping()
            self.is_available = True
        except:
            self.is_available = False
            self.backup_store = {} # Fallback cho local dev
            logger.warning("⚠️ Redis offline - Falling back to local memory")

    def _get_key(self, sid: str) -> str:
        return f"agent:session:{sid}"

    def get_history(self, sid: str) -> List[dict]:
        if self.is_available:
            data = self.client.get(self._get_key(sid))
            return json.loads(data) if data else []
        return self.backup_store.get(sid, [])

    def update_history(self, sid: str, messages: List[dict], ttl: int = 3600):
        # Giữ 10 turns gần nhất (20 messages)
        truncated = messages[-20:]
        if self.is_available:
            self.client.setex(self._get_key(sid), ttl, json.dumps(truncated))
        else:
            self.backup_store[sid] = truncated

# --- FastAPI App ---
app = FastAPI(title="Stateless AI Agent Pro")
store = SessionStore(REDIS_URL)

@app.post("/chat")
async def chat(body: ChatRequest):
    # 1. Định danh session
    sid = body.session_id or str(uuid.uuid4())
    
    # 2. Lấy toàn bộ history 1 lần duy nhất (Stateless Read)
    history = store.get_history(sid)
    
    # 3. Chuẩn bị context cho AI
    user_msg = Message(role="user", content=body.question)
    history.append(user_msg.model_dump())
    
    # 4. Gọi AI (giả lập)
    from utils.mock_llm import ask
    ai_response = ask(body.question)
    
    ai_msg = Message(role="assistant", content=ai_response)
    history.append(ai_msg.model_dump())
    
    # 5. Lưu lại state mới vào Redis (Stateless Write)
    store.update_history(sid, history)
    
    return {
        "session_id": sid,
        "answer": ai_response,
        "served_by": INSTANCE_ID,
        "history_count": len(history)
    }

@app.get("/health")
def health():
    return {
        "status": "ok" if store.is_available else "degraded",
        "instance": INSTANCE_ID,
        "storage": "redis" if store.is_available else "local_memory"
    }
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)