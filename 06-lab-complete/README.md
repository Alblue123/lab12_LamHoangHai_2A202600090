# Hướng dẫn Cài đặt & Triển khai VinBank Agent 🚀

Chào mừng bạn đến với phiên bản triền khai môi trường sản phẩm (production release) của Trợ lý AI VinBank! Hệ thống này đã chuyển từ bản nguyên mẫu Jupyter cơ bản thành một kiến trúc microservice cực kỳ mạnh mẽ, không lưu trạng thái (stateless), được bảo vệ bằng cơ chế giới hạn truy cập rate limit thông qua Redis!

## Kiến trúc Công nghệ (Architecture Stack)
- **FastAPI**: Lõi xử lý Backend bằng Python.
- **Gemini (`google-genai`)**: Xử lý ngôn ngữ tự nhiên thông qua AI model (`gemini-2.5-flash-lite`).
- **Redis**: Phân tán để xử lý Lịch sử Chat, Rate Limits và Quản lý Ngân sách.
- **Nginx & Docker**: Điều phối bằng `docker-compose` phân tải (Load balancer).
- **Railway**: Triển khai định tuyến Cloud tự động.

## Thiết lập & Chạy Thử (Setup & Testing)

### 1. Cấu hình Biến Môi trường
Bắt buộc không bao giờ được push file `.env` chứa mật khẩu nội bộ! Hãy nhân bản file cấu hình trắng:
```bash
cp .env.example .env
```
Đảm bảo bạn đã dán API thật của `GEMINI_API_KEY` cũng như khoá tuỳ chỉnh của `AGENT_API_KEY` vào trong file `.env` đó.

### 2. Chạy dưới Localhost
Xây dựng hạ tầng hoàn chỉnh trên máy chủ thật:
```bash
docker-compose up --build -d --scale agent=3
```
Chạy thử qua Load Balancer (Nginx) mặc định ở cổng 80:
```bash
curl http://localhost/health
```

### 3. Giao diện Cửa sổ Web
Sau khi chạy thành công (hoặc xem trang Railway công khai), bạn có thể vào thẳng root URL `http://localhost/` hoặc `https://<YOUR-RAILWAY-DOMAIN>` bằng trình duyệt web. 
Đăng nhập tại ô nhập khóa bằng các Mock Token đa danh tính an toàn:
- Dùng `key-vip` (truy cập vai trò "user_albert")
- Dùng `key-test` (truy cập vai trò "user_sara")
