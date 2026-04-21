# Hotel Module CLI (Python)

Ứng dụng Python nhỏ mô phỏng các luồng chính của module **Hotel** dựa trên tài liệu báo cáo:
- Tìm kiếm khách sạn theo địa điểm, số khách, ngày ở
- Lọc theo giá, sao, tiện nghi
- Đặt phòng với validation boundary (1..5 phòng)
- Mô phỏng thanh toán và trả kết quả xác nhận

## Chạy ứng dụng

```bash
python app.py --help
```

## Ví dụ tìm kiếm

```bash
python app.py search \
  --location "Da Nang" \
  --checkin 2026-05-10 \
  --checkout 2026-05-12 \
  --guests 2 \
  --min-price 500000 \
  --max-price 1000000 \
  --amenity wifi
```

## Ví dụ đặt phòng

```bash
python app.py book \
  --hotel-id HTL001 \
  --room-type standard \
  --rooms 1 \
  --checkin 2026-05-10 \
  --checkout 2026-05-12 \
  --guests 2 \
  --card-number 4111111111111111 \
  --cvv 123
```
