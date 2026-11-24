# AutoClicker

Phần mềm Auto Click và Macro.

---

## 🌟 Tính năng chính

- **Auto Click**: Tốc độ từ 1ms đến nhiều giờ (lên đến 1000+ CPS), có sẵn các mức chọn nhanh (`10`, `50`, `100`, `MAX`).
- **Macro đa điểm**: Tự động ghi lại thao tác chuột (Record) hoặc thêm từng bước tọa độ mong muốn.
- **Giữ nguyên chuột (Restore Cursor)**: Tự động đưa con trỏ chuột về lại vị trí cũ sau khi click, giúp bạn thoải mái làm việc khác.
- **Chọn tọa độ thông minh**: Nhấp chuột trực tiếp vào điểm bất kỳ trên màn hình để lấy tọa độ.
- **Chống phát hiện (Jitter)**: Tự tạo độ lệch ngẫu nhiên thời gian và vị trí để vượt qua cơ chế chống bot.

---

## ⌨️ Phím tắt mặc định

| Phím tắt | Chức năng |
| :---: | :--- |
| **`F6`** | Bật / Tắt Auto Click |
| **`F7`** | Bật / Tắt chạy Macro |

---

## 🚀 Hướng dẫn sử dụng

### 1. Dùng trực tiếp (Khuyên dùng)
Chạy trực tiếp file:
👉 **`AutoClicker.exe`** (dùng ngay, không cần cài đặt gì thêm). Cài đặt và hồ sơ được lưu trong thư mục `profiles/` cạnh file exe.

### 2. Build từ mã nguồn (Rust)
Cần cài [Rust](https://rustup.rs) (toolchain MSVC).
```bash
cargo build --release
```
File exe nằm ở `target/release/autoclicker.exe`; copy ra thư mục gốc và đổi tên thành `AutoClicker.exe` để dùng chung thư mục `profiles/`.

### 3. Chạy test
```bash
cargo test
```
