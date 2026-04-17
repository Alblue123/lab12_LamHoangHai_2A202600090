# Thông tin Triển khai (Deployment Information)

## Public URL
https://fast-api-agent-production.up.railway.app/

## Nền tảng (Platform)
Railway

## Các Lệnh Kiểm tra (Test Commands)

### Kiểm tra Sức khỏe (Health Check)
```bash
curl https://fast-api-agent-production.up.railway.app/health
# Kết quả mong đợi: {"status": "ok"}
```

### Kiểm tra API (với xác thực Authentication Mới bằng Mock ID)
```bash
# Lệnh gửi API với Token của người dùng 'key-vip'
curl -X POST https://fast-api-agent-production.up.railway.app/ask \
  -H "X-API-Key: key-vip" \
  -H "Content-Type: application/json" \
  -d '{"question": "Xin chào! Tôi muốn tạo một tài khoản ngân hàng."}'
```
*(Ghi chú: Lệnh Post đã không còn cần chèn `user_id` giả mạo vào payload nữa, do backend đã tự tin cậy khóa `key-vip` để tự động định danh khách hàng)*

## Các Biến Môi trường Đã thiết lập (Environment Variables Set)
- `PORT` = `8000`
- `ENVIRONMENT` = `production`
- `REDIS_URL` = `redis://default:xxx@redis.railway.internal:6379`
- `AGENT_API_KEY` = `my-super-secret-key` (Đã được tích hợp vào master_auth)
- `LOG_LEVEL` = `INFO`
- `GEMINI_API_KEY` = `AQ.Ab8RN6K....`

## Ảnh chụp màn hình (Screenshots)
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
