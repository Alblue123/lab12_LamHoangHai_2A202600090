# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. Pb1: Hardcode API Key and URL
2. Pb2: No config management (env vars, .env, etc.)
3. Pb3: Using `print()` for logging
4. Pb4: Missing health check endpoint
5. Pb5: Fixed port and host configuration
6. Pb6: No graceful shutdown

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Tránh lộ API keys trên GitHub. Dễ dàng thay đổi cấu hình giữa các môi trường (local, prod) mà không cần sửa code. |
| Health check | Không có | Có (`/health`) | Giúp các nền tảng đám mây (Kubernetes, Railway) biết ứng dụng có bị "treo" hay không để tự động khởi động lại (restart) container. |
| Logging | `print()` | JSON | Log dạng JSON giúp các hệ thống quản lý (Loki, Datadog) dễ dàng parse, tìm kiếm và cảnh báo lỗi, thay vì đọc text lộn xộn. |
| Shutdown | Đột ngột | Graceful | Cho phép server hoàn thành nốt các request đang xử lý dở dang trước khi tắt, tránh lỗi "Connection Reset" cho user khi deploy bản mới. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image là gì?** `python:3.11` — Là image nhà phát triển đã cài sẵn thư viện cần thiết.
2. **Working directory là gì?** `/app` — Tất cả những gì thực hiện đều được lưu trữ/copy under folder này.
3. **Tại sao COPY requirements.txt trước?** Nếu bạn copy `requirements.txt` và chạy `pip install` **trước**, Docker sẽ lưu lại kết quả này (cache layer). Lần sau bạn sửa code `app.py` và build lại, Docker thấy `requirements.txt` không đổi nên nó bỏ qua bước tải thư viện tốn thời gian, và chỉ copy lại phần code mới.
4. **CMD vs ENTRYPOINT khác nhau thế nào?** `CMD`: Lệnh mặc định — **Dễ bị ghi đè** bởi lệnh mới khi chạy `docker run`. `ENTRYPOINT`: Lệnh cố định — **Không bị ghi đè**. Những gì bạn gõ thêm sau `docker run` chỉ được tính là **tham số** truyền vào.

### Exercise 2.2: Build và run

**Image size quan sát được:** 1.66GB

```bash
docker images my-agent:develop
```

### Exercise 2.3: Multi-stage build

- **Stage 1 làm gì?** Stage 1 tải các thư viện về và biên dịch.
- **Stage 2 làm gì?** Stage 2 copy các thư viện đã được biên dịch (từ Stage 1 sang).
- **Tại sao image nhỏ hơn?** Docker chỉ lấy các file ở Stage 2 để build image cuối, bỏ lại toàn bộ công cụ biên dịch và cache ở Stage 1.

Image size comparison:
- Develop: ~1.66 GB
- Production: ~165 MB
- Chênh lệch: ~90% nhỏ hơn

### Exercise 2.4: Docker Compose stack

Services nào được start? Chúng communicate thế nào?

Bốn services giao tiếp với nhau trong một mạng nội bộ (`internal` network) hoàn toàn khép kín: **Nginx** là cửa ngõ duy nhất đón yêu cầu từ Internet ở cổng 80, sau đó chuyển tiếp thẳng cho **Agent** (ứng dụng AI trung tâm); từ đây, chỉ có duy nhất Agent mới có quyền nói chuyện với **Redis** (để kiểm tra bộ nhớ đệm/giới hạn) và **Qdrant** (để tìm kiếm dữ liệu), tạo thành một luồng xử lý an toàn và bảo mật.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- **URL:** https://fast-api-agent-production.up.railway.app
- **Screenshot:** [Deployment dashboard](screenshots/dashboard.png)

### Exercise 3.2: render.yaml vs railway.toml

- **Render (`render.yaml`)** cấu hình toàn bộ kiến trúc phức tạp (Web, Database, Workers) thành một hệ thống thống nhất.
- **Railway (`railway.toml`)** cực kỳ tinh gọn, chủ yếu dùng để ghi đè lệnh chạy hoặc tinh chỉnh nhanh cho một ứng dụng cụ thể.
- **Tóm lại:** Dùng Render cho dự án lớn cần quản lý hạ tầng chi tiết, dùng Railway để deploy siêu tốc và đơn giản.

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

- **API key được check ở đâu?** API key được kiểm tra bên trong hàm `verify_api_key()`.
- **Điều gì xảy ra nếu sai key?**
  - Nếu gửi request **không có** header `X-API-Key` → Server trả về lỗi **401 Unauthorized** (Missing API key).
  - Nếu gửi request **có header nhưng sai giá trị** → Server trả về lỗi **403 Forbidden** (Invalid API key).
- **Làm sao rotate key?**
  1. Lên nền tảng cloud (Railway, Render, AWS...) hoặc mở file `.env`.
  2. Sửa giá trị của biến `AGENT_API_KEY` thành một chuỗi ngẫu nhiên mới.
  3. **Khởi động lại (Restart)** container/ứng dụng để nó đọc lại biến môi trường mới.

### Exercise 4.2: JWT authentication

JWT flow: Gọi `POST /token` với username/password → nhận JWT token → gắn vào header `Authorization: Bearer <token>` cho các request tiếp theo.

Token lấy được:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0MTgyNzIsImV4cCI6MTc3NjQyMTg3Mn0.ZCzYGiVbPDuRNcWhBq60-U7Pe6GtOGF6NXtmJMJfGFs
```

### Exercise 4.3: Rate limiting

- **Algorithm nào được dùng?** Sliding window counter
- **Limit là bao nhiêu requests/minute?** 10 requests / 1 phút
- **Làm sao bypass limit cho admin?** Nếu là Admin, bạn chỉ cần bỏ qua việc gọi hàm `check()` của RateLimiter — không thêm request vào cửa sổ đếm.

### Exercise 4.4: Cost guard implementation

Logic triển khai trong `cost_guard.py`:
- Mỗi user có budget $10/tháng.
- Track spending trong Redis với key: `budget:{user_id}:{YYYY-MM}`.
- Mỗi request ước tính chi phí $0.01. Nếu `current + estimated_cost > 10` thì raise HTTP 402.
- Dùng `r.incrbyfloat(key, estimated_cost)` để cộng dồn và `r.expire(key, 32*24*3600)` để tự reset sau ~1 tháng.

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    try:
        r.ping()
        db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return JSONResponse(status_code=503, content={"status": "not ready"})
```

- `/health` (Liveness probe): Xác nhận process còn sống, trả về 200 nếu OK.
- `/ready` (Readiness probe): Kiểm tra Redis và database có kết nối được không, trả về 200 nếu sẵn sàng, 503 nếu chưa ready.

### Exercise 5.2: Graceful shutdown

Xử lý SIGTERM với `signal.signal(signal.SIGTERM, shutdown_handler)` để dừng nhận request mới và hoàn thành hết request đang xử lý trước khi đóng app. Trong FastAPI dùng `lifespan` context manager để cleanup.

### Exercise 5.3: Stateless design

**Anti-pattern (State trong memory):**
```python
conversation_history = {}  # Mất khi instance restart

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
```

**Correct (State trong Redis):**
```python
@app.post("/ask")
def ask(user_id: str, question: str):
    history = r.lrange(f"history:{user_id}", 0, -1)
```

**Tại sao?** Vì khi scale ra nhiều instances, mỗi instance có memory riêng — nếu request được route sang instance khác, lịch sử hội thoại sẽ bị mất. Redis là trung gian dùng chung cho tất cả instances.

### Exercise 5.4: Load balancing

Chạy `docker compose up --scale agent=3`:
- 3 agent instances được start song song.
- Nginx phân tán requests theo round-robin.
- Nếu 1 instance die, traffic tự động chuyển sang instances khác.

### Exercise 5.5: Test stateless

Script `test_stateless.py`:
1. Gọi API để tạo conversation.
2. Kill random instance.
3. Gọi tiếp — conversation vẫn còn vì state lưu trong Redis, không phải trong memory instance.
