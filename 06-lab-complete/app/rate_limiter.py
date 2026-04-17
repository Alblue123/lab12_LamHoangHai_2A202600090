import time
import redis
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def check_rate_limit(user_id: str):
    now = time.time()
    window = 60
    max_requests = settings.RATE_LIMIT_PER_MINUTE
    key = f"rate_limit:{user_id}"
    
    # Clean old requests
    r.zremrangebyscore(key, 0, now - window)
    
    # Count current requests in the window
    current_count = r.zcard(key)
    if current_count >= max_requests:
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    # Add new request
    r.zadd(key, {str(now): now})
    r.expire(key, window)
