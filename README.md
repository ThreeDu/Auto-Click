# AutoClicker

Tool auto click và macro chuột đa điểm cho Windows, giao diện tối đơn giản, tốc độ cao (lên đến 1000+ CPS).

---

## Cách cài đặt & Chạy

Yêu cầu: Đã cài **Python 3.10+** trên Windows.

```bash
# 1. Cài đặt thư viện cần thiết
pip install -r requirements.txt

# 2. Chạy ứng dụng
python main.py
```

---

## Phím tắt mặc định

| Phím tắt | Chức năng |
|:---|:---|
| **F6** | Bật / Tắt Auto Click |
| **F7** | Bật / Tắt Macro đa điểm |

*(Có thể đổi phím tắt trong tab **Settings**)*

---

## Tính năng chính

- **Auto Click tốc độ cao**: Chỉnh thời gian linh hoạt (giờ, phút, giây, mili-giây) hoặc chọn nhanh `10`, `50`, `100`, `MAX (1ms)`.
- **Macro đa điểm**: Tự tạo chuỗi click nhiều vị trí trên màn hình hoặc nhấn **Record** để ghi lại thao tác click thực tế.
- **Tùy chọn vị trí**: Click theo con trỏ chuột hoặc khóa tọa độ cố định (có công cụ chấm tọa độ nhanh).
- **Chống phát hiện (Jitter)**: Tạo độ lệch ngẫu nhiên về thời gian và vị trí để tránh bị game/web phát hiện bot.
- **Mini HUD**: Thanh trạng thái nhỏ gọn nổi trên màn hình game theo dõi số click và CPS.
- **Quản lý Profile**: Lưu và tải cấu hình cho từng game hoặc tác vụ khác nhau.
- **Chạy nền**: Thu nhỏ xuống khay hệ thống (System Tray) tiện lợi.

---

## Đóng gói thành file .exe (Không cần Python)

Chạy file:
```cmd
build_nuitka.bat
```
File `.exe` sẽ được tạo trong thư mục `main.dist/AutoClicker.exe`.
