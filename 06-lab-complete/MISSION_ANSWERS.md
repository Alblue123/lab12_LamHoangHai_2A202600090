# Đáp án Bài tập Lab Ngày 12 (Mission Answers)

## Phần 1: Localhost vs Production (Môi trường cục bộ và Môi trường sản xuất)

### Bài tập 1.1: Các Lỗi phản khuôn mẫu (Anti-patterns) được phát hiện
1. Kiến trúc ban đầu kết hợp chung code và config cùng chỗ thay vì tách biệt rõ ràng các môi trường qua cấu trúc `.env`.
2. Đầu vào API tin cậy trực tiếp field `user_id` được gửi từ Frontend, là một lỗi bảo mật nghiêm trọng (Broken Object Level Authorization). Bản chính thức đã thay thế bằng cách gắn chết Token API (`key-vip`) trực tiếp vào Danh tính (Identity Auth Override).

### Bài tập 1.3: Bảng so sánh
| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| Config  | Biến code cứng / Dict thường | Pydantic `BaseSettings` + 12-factor Validations | Pydantic tự động ép kiểu dữ liệu và từ chối khởi động app nếu môi trường Production bị quên chưa xóa chuỗi config bảo vệ `dev-key`. |
| State | Quản lý API bằng bộ nhớ Dict trên RAM cá nhân | Sử dụng máy chủ Redis bên ngoài | Ngăn tình trạng mất lịch sử user khi 3 cụm Agent tái khởi động, chia sẻ được chung giới hạn Rate-Limit dồn dập. |
| Logging | Sử dụng lệnh `print()` thông thường | Thư viện `logging` xuất bản dạng JSON có cấu trúc | Giúp hệ thống server dễ dàng thu gỡ tự động từng thuộc tính lỗi. |

## Phần 2: Docker

### Bài tập 2.1: Câu hỏi về Dockerfile
1. Base image (Ảnh gốc): `python:3.11-slim` 
2. Working directory (Thư mục làm việc): `/app`
3. Tại sao phải sử dụng Multi-stage builds? Nó giúp cô lập các công cụ dùng để tải/build package (như trình biên dịch PIP, cache build) tách khép xa khỏi môi trường run cuối (runtime). Container cuối được an toàn tránh bề mặt tấn công rộng và thu hẹp thể tích máy ảo.

### Bài tập 2.3: So sánh kích thước Image
- Develop: ~1200 MB (khi dùng chung bản Python C-compiler/khoa học rộng)
- Production: ~165 MB (Chỉ duy trì thư mục `venv`)
- Difference (Khác biệt): ~86%

## Phần 4: Bảo mật API & Nhận diện danh tính

### Bài tập 4.4: Cách triển khai Cost guard & Đa người dùng
Hệ thống sử dụng mô phỏng Đa người dùng (Multi-tenant MOCK_DB). Mỗi khóa Token (`key-vip` hoặc `key-test`) đại diện cụ thể cho một User. Khi truy cập, User sẽ bị trừ thẳng vào biến `$10 USD / tháng` lưu bằng `Redis Time-To-Live (TTL)` trong vòng 30 ngày từ chính danh tính của khóa Token đó, không cho phép User tùy tiện đánh lừa truy vấn Payload bằng tên giả.

## Phần 5: Mở rộng ngang & Độ tin cậy (Scaling & Reliability)

### Bài tập 5.1-5.5: Ghi chú triển khai
Hệ thống microservice sử dụng Gemini `2.5-flash-lite` đã được nâng cấp API Key nội bộ hoạt động trơn tru. Hệ thống tự động bắt tín hiệu `Depends` trên FastAPI chặn `401 Unauthorized` đối chiếu từ Mock Database trước khi chuyển về Rate Limiter. 
Khi gặp vấn đề treo do Railway tắt server (redeploys), tiến trình nhận vòng đời `FastAPI lifespan (SIGTERM)` sẽ xả nốt các bộ đệm đang giữ rồi mới đóng máy con.
