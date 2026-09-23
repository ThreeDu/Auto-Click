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
👉 **`AutoClicker.exe`** (dùng ngay, không cần cài đặt Python hay phần mềm phụ trợ).

### 2. Chạy từ mã nguồn Python
```bash
pip install -r requirements.txt
python main.py
```

### 3. Đóng gói lại file `.exe`
Chạy file script có sẵn:
👉 **`build_nuitka.bat`**
