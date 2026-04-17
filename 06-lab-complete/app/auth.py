from fastapi import Header, HTTPException
from .config import settings

MOCK_USERS = {
    "key-vip": "user_albert",
    "key-test": "user_sara",
    settings.AGENT_API_KEY: "admin_master"
}

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid API Key. Not found in Mock DB.")
    # Return the mapped mock user identity
    return MOCK_USERS[x_api_key]
