import time
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Response
from pydantic import BaseModel

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit, r as redis_client
from .cost_guard import check_budget
from .guards import InputGuardrails, OutputGuardrails

# Optional Gemini integration
try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None
except ImportError:
    client = None

# Structured JSON logging setup
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)

logger = logging.getLogger("agent")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(settings.LOG_LEVEL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down gracefully. Finishing pending requests...")
    # Add cleanup logic if necessary (Lifespan natively catches SIGTERM correctly)
    
app = FastAPI(lifespan=lifespan)

@app.get("/")
def get_ui():
    import os
    filepath = os.path.join(os.path.dirname(__file__), "index.html")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/html")
    except FileNotFoundError:
        return Response(content="<h1>UI not found</h1>", media_type="text/html")

input_guard = InputGuardrails()
output_guard = OutputGuardrails()

# Pydantic schemas
class AskRequest(BaseModel):
    question: str
    user_id: str

class AskResponse(BaseModel):
    status: str
    response: str
    latency: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        if redis_client.ping():
            return {"status": "ready"}
    except Exception as e:
        logger.error(f"Redis not ready: {str(e)}")
        return Response(status_code=503, content=json.dumps({"status": "not ready"}))
    return Response(status_code=503, content=json.dumps({"status": "not ready"}))

@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    auth_user: str = Depends(verify_api_key)
):
    start_time = time.time()
    # Force user identity to lock onto the token holder (override unsafe JSON payload)
    user_id = auth_user if auth_user != "admin_master" else request.user_id

    logger.info(f"Received request from authenticated user: {user_id}")
    
    try:
        # Rate Limiting
        check_rate_limit(user_id)
        
        # Budget Check
        check_budget(user_id)
        
        # Input Guard
        is_safe, msg = input_guard.check(question)
        if not is_safe:
            logger.warning(f"Input blocked for user {user_id}: {msg}")
            return AskResponse(status="blocked", response=msg, latency=time.time() - start_time)

        # Retrieve History from Redis (last 5 messages)
        history_key = f"history:{user_id}"
        history = [msg.decode('utf-8') if isinstance(msg, bytes) else msg for msg in redis_client.lrange(history_key, 0, 4)]
        
        # Mock LLM generation or real Gemini LLM
        if client and settings.GEMINI_API_KEY:
            contents = []
            sys_instruct = "You are a helpful customer service assistant for VinBank. Keep answers concise."
            for h in history[::-1]:
                contents.append(h)
            contents.append(question)
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents="\n".join(contents),
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruct,
                        temperature=0.3
                    )
                )
                raw_response = response.text
            except Exception as e:
                logger.error(f"Gemini error: {str(e)}")
                raw_response = f"This is a mock fallback response because the LLM failed."
        else:
            # Mock canned response
            raw_response = f"This is a mock response from VinBank about your query: '{question}'"
            time.sleep(0.5)

        # Output Guard
        is_safe, redacted_response, msg = output_guard.check_and_redact(raw_response)

        # Save to Redis
        redis_client.lpush(history_key, redacted_response)
        redis_client.lpush(history_key, question)
        redis_client.ltrim(history_key, 0, 9) # Keep last 10 messages (5 pairs)
        
        logger.info(f"Successfully processed request for user: {user_id}")
        return AskResponse(status="success", response=redacted_response, latency=time.time() - start_time)

    except HTTPException as he:
        logger.warning(f"HTTP Exception for user {user_id}: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
