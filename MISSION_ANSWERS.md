# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. API key hardcode
2. Không có quản lý cấu hình (env vars, .env, etc.)
3. Sử dụng `print()` để logging thay vì công cụ chuẩn
4. Thiếu health check endpoint
5. Port và host configuration bị cố định (fixed)
6. Không xử lý Graceful shutdown

### Exercise 1.3: Comparison table
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config | Hardcode | Env vars | Tránh lộ API keys trên GitHub. Dễ dàng thay đổi cấu hình giữa các môi trường (local, prod) mà không cần sửa code. |
| Health check | Không có | Có (`/health`) | Giúp các nền tảng đám mây (Kubernetes, Railway) biết ứng dụng có bị "treo" hay không để tự động khởi động lại (restart) container. |
| Logging | `print()` | JSON | Log dạng JSON giúp các hệ thống quản lý (Loki, Datadog) dễ dàng parse, tìm kiếm và cảnh báo lỗi, thay vì đọc text lộn xộn. |
| Shutdown | Đột ngột | Graceful | Cho phép server hoàn thành nốt các request đang xử lý dở dang trước khi tắt, tránh lỗi "Connection Reset" cho user khi deploy bản mới. |

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: `python:3.11` - Là image nhà phát triển đã cài sẵn thư viện cần thiết.
2. Working directory: `/app` - Tất cả những gì thực hiện đều được lưu trữ/copy under folder này.
3. Tại sao COPY requirements.txt trước? Nếu bạn copy `requirements.txt` và chạy `pip install` trước, Docker sẽ lưu lại kết quả này (cache layer). Lần sau bạn sửa code app.py và build lại, Docker bỏ qua bước tải thư viện tốn thời gian, và chỉ copy lại phần code mới.
4. CMD vs ENTRYPOINT khác nhau thế nào? `CMD` là lệnh mặc định — Dễ bị ghi đè bởi lệnh mới khi chạy docker run. `ENTRYPOINT` là lệnh cố định — Không bị ghi đè, những tham số sau docker run chỉ được truyền vào như arguments.

### Exercise 2.3: Image size comparison
- Develop: ~1.66 GB
- Production: ~165 MB
- Difference: Nhỏ hơn rất nhiều (~90% tiết kiệm không gian) do Docker chỉ lấy các file cần thiết từ Builder Stage (Stage 1) qua Runtime Stage (Stage 2) và bỏ lại các công cụ biên dịch không cần thiết.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://fast-api-agent-production.up.railway.app
- Screenshot: [Deployment dashboard](screenshots/dashboard.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- **Exercise 4.1**: API key được kiểm tra bên trong hàm `verify_api_key()`. Nếu không có key, server trả về `401 Unauthorized`. Nếu sai key, trả về `403 Forbidden`.
- **Exercise 4.2**: Lấy JWT token từ `/token` bằng cách gửi username/password, sau đó gắn token vào header `Authorization: Bearer <token>` để xác thực các truy vấn API.
- **Exercise 4.3**: Rate Limiter sử dụng thuật toán Sliding Window Counter. Giới hạn là 10 requests/phút. Admin có thể bypass giới hạn bằng cách không gọi hàm check() của RateLimiter.

### Exercise 4.4: Cost guard implementation
Triển khai Cost Guard bằng cách track mức chi tiêu trên Redis với key là `budget:{user_id}:{month_key}`. Mỗi user có một mức ngân sách tối đa là $10/tháng. Khi user gọi API, app tính estimated cost và kiểm tra nếu chi phí hiện tại + estimated_cost > 10 thì trả về False (từ chối). Nếu được, ghi đè cộng dồn vào Redis và cài đặt TTL là 32 ngày (`r.expire(key, 32*24*3600)`).

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Exercise 5.1**: Tạo Liveness probe (`/health`) trả về `200 OK` để xác nhận container sống. Readiness probe (`/ready`) thực hiện ping thử đến database (VD: Redis `r.ping()`) báo hiệu sẵn sàng xử lý traffic.
- **Exercise 5.2**: Xử lý SIGTERM với `signal.signal(signal.SIGTERM, shutdown_handler)` để dừng nhận request mới và xử lý hết request đang chạy trước khi đóng app.
- **Exercise 5.3**: Chuyển đổi trạng thái bộ nhớ State từ memory nội bộ của Python (như Dictionary `conversation_history`) sang Redis lưu trữ độc lập để đảm bảo Stateless design (dữ liệu đồng bộ trên nhiều agents).
- **Exercise 5.4**: Nginx đóng vai trò là Load Balancer, nhận requests tại cổng 80 và phân bổ điều hướng qua mạng nội bộ cho 3 Agents chạy ngầm.
- **Exercise 5.5**: Test Stateless Design xác nhận khi kill một instance giữa chừng, lịch sử hội thoại không bị gián đoạn vì nó đã được truy xuất độc lập qua Redis.
