# Deployment Information

## Public URL

<https://fast-api-agent-production.up.railway.app>

## Platform

Railway

## Test Commands

### Health Check

```bash
curl https://fast-api-agent-production.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)

```bash
curl -X POST https://fast-api-agent-production.up.railway.app/ask \
  -H "X-API-Key: my-super-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the savings interest rate?"}'
```

## Environment Variables Set

- PORT
- ENVIRONMENT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL
- GEMINI_API_KEY

## Screenshots

- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
