import os
import time
import signal
import sys
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# Giả lập các client (Trong thực tế bạn sẽ import từ file database.py, redis.py)
class MockClient:
    def ping(self): return True
    def execute(self, query): return True

r = MockClient()  # Mock Redis
db = MockClient() # Mock Database

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Trạng thái toàn cục
is_shutting_down = False
is_model_loaded = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle: Startup và Shutdown"""
    global is_model_loaded, is_shutting_down
    
    # --- STARTUP ---
    logger.info("--- STARTUP: Loading resources ---")
    time.sleep(1)  # Giả lập load model nặng
    is_model_loaded = True
    logger.info("✅ Startup complete: Agent is ready")
    
    yield
    
    # --- SHUTDOWN ---
    is_shutting_down = True
    is_model_loaded = False
    logger.info("--- SHUTDOWN: Cleaning up connections ---")
    # Giả lập thời gian chờ để hoàn thành các request dở dang
    time.sleep(2) 
    logger.info("✅ Cleanup complete")

app = FastAPI(title="Reliable Agent", lifespan=lifespan)

# ============================================================
# EXERCISE 5.1: HEALTH CHECKS
# ============================================================

@app.get("/health")
def health():
    """Liveness probe — 'Mày còn thở không?'"""
    # Nếu process còn chạy đến đây được, nghĩa là nó còn sống
    return {"status": "ok", "timestamp": datetime.now(timezone.utc)}

@app.get("/ready")
def ready():
    """Readiness probe — 'Mày đã sẵn sàng làm việc chưa?'"""
    # 1. Check if model is loaded
    if not is_model_loaded or is_shutting_down:
        raise HTTPException(status_code=503, detail="Agent is starting up or shutting down")

    try:
        # 2. Check Redis connection
        r.ping()
        # 3. Check Database connection
        db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "dependencies": {"redis": "ok", "db": "ok"}
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "Dependency failure"}
        )

# ============================================================
# EXERCISE 5.2: GRACEFUL SHUTDOWN
# ============================================================

def shutdown_handler(signum, frame):
    """Xử lý tín hiệu SIGTERM từ Docker/K8s"""
    global is_shutting_down
    logger.info(f"🚩 Received signal {signum}. Initiating graceful exit...")
    
    # Đánh dấu không nhận traffic mới (Readiness probe sẽ bắt đầu fail)
    is_shutting_down = True
    
    # Uvicorn mặc định bắt SIGTERM và sẽ gọi lifespan shutdown.
    # Chúng ta không cần gọi sys.exit(0) ở đây vì sẽ làm ngắt quãng uvicorn.

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# ============================================================
# EXERCISE 5.3: STATELESS DESIGN
# ============================================================

# ❌ Anti-pattern: State lưu trong memory
# conversation_history = {} 

import asyncio
@app.post("/ask")
async def ask_agent(user_id: str, question: str):
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Server is shutting down")
    
    logger.info(f"Processing for {user_id}: {question}")
    
    # ✅ Correct pattern: State lưu tập trung ở Redis (Stateless)
    # Lấy lịch sử hội thoại từ Redis thay vì memory
    # history = r.lrange(f"history:{user_id}", 0, -1)
    
    await asyncio.sleep(5)  # Giả lập một tác vụ AI nặng (5 giây)
    
    # Giả lập ghi lịch sử mới vào Redis
    # r.rpush(f"history:{user_id}", question)
    
    return {"answer": f"Processed: {question}"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000,
        # ✅ Thời gian chờ request cuối hoàn thành trước khi kill hẳn process
        timeout_graceful_shutdown=30 
    )