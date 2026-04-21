from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from typing import Iterable


@dataclass(frozen=True)
class Room:
    name: str
    price_per_night: int
    capacity: int
    available_rooms: int
    amenities: tuple[str, ...]


@dataclass(frozen=True)
class Hotel:
    hotel_id: str
    name: str
    location: str
    stars: int
    amenities: tuple[str, ...]
    rooms: tuple[Room, ...]


HOTELS: tuple[Hotel, ...] = (
    Hotel(
        hotel_id="HTL001",
        name="Da Nang Beach View",
        location="Da Nang",
        stars=4,
        amenities=("wifi", "pool", "parking"),
        rooms=(
            Room("standard", 650_000, 2, 5, ("wifi", "ac")),
            Room("family", 980_000, 4, 2, ("wifi", "ac", "kitchen")),
        ),
    ),
    Hotel(
        hotel_id="HTL002",
        name="Hoi An River Stay",
        location="Hoi An",
        stars=3,
        amenities=("wifi", "breakfast"),
        rooms=(
            Room("standard", 520_000, 2, 4, ("wifi",)),
            Room("deluxe", 820_000, 3, 2, ("wifi", "balcony")),
        ),
    ),
    Hotel(
        hotel_id="HTL003",
        name="Nha Trang Ocean Light",
        location="Nha Trang",
        stars=5,
        amenities=("wifi", "pool", "spa", "parking"),
        rooms=(
            Room("standard", 900_000, 2, 6, ("wifi", "ac")),
            Room("suite", 1_600_000, 4, 1, ("wifi", "ac", "bathtub")),
        ),
    ),
)


def parse_iso_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Ngày không hợp lệ: {raw}. Dùng YYYY-MM-DD.") from exc


def validate_stay_dates(checkin: str, checkout: str) -> tuple[date, date]:
    ci = parse_iso_date(checkin)
    co = parse_iso_date(checkout)
    if co <= ci:
        raise ValueError("Checkout phải sau checkin.")
    return ci, co


def nights_between(checkin: date, checkout: date) -> int:
    return (checkout - checkin).days


def find_hotel(hotel_id: str) -> Hotel:
    for hotel in HOTELS:
        if hotel.hotel_id == hotel_id:
            return hotel
    raise ValueError(f"Không tìm thấy hotel_id={hotel_id}")


def find_room(hotel: Hotel, room_name: str) -> Room:
    for room in hotel.rooms:
        if room.name == room_name:
            return room
    raise ValueError(f"Không tìm thấy loại phòng '{room_name}' ở {hotel.name}")


def hotel_min_room_price(hotel: Hotel) -> int:
    return min(r.price_per_night for r in hotel.rooms)


def search_hotels(
    location: str,
    guests: int,
    min_price: int | None,
    max_price: int | None,
    stars: int | None,
    amenity: str | None,
) -> list[dict]:
    results: list[dict] = []
    for hotel in HOTELS:
        if hotel.location.lower() != location.lower():
            continue
        if stars is not None and hotel.stars != stars:
            continue
        if amenity is not None and amenity not in hotel.amenities:
            continue

        matching_rooms = [r for r in hotel.rooms if r.capacity >= guests and r.available_rooms > 0]
        if not matching_rooms:
            continue

        min_room_price = min(r.price_per_night for r in matching_rooms)
        if min_price is not None and min_room_price < min_price:
            continue
        if max_price is not None and min_room_price > max_price:
            continue

        results.append(
            {
                "hotel_id": hotel.hotel_id,
                "name": hotel.name,
                "location": hotel.location,
                "stars": hotel.stars,
                "starting_price": min_room_price,
                "amenities": hotel.amenities,
            }
        )
    return results


def process_payment(amount: int, card_number: str, cvv: str, retries: int = 2) -> dict:
    if len(cvv) != 3 or not cvv.isdigit():
        return {"status": "failed", "reason": "CVV không hợp lệ"}
    if len(card_number) < 12 or not card_number.isdigit():
        return {"status": "failed", "reason": "Số thẻ không hợp lệ"}

    for attempt in range(1, retries + 1):
        if attempt == 1 and card_number.startswith("9"):
            continue
        return {"status": "success", "paid_amount": amount, "attempts": attempt}

    return {"status": "failed", "reason": "Timeout payment gateway"}


def create_booking(
    hotel_id: str,
    room_type: str,
    rooms: int,
    checkin: str,
    checkout: str,
    guests: int,
    card_number: str,
    cvv: str,
) -> dict:
    ci, co = validate_stay_dates(checkin, checkout)
    if rooms < 1 or rooms > 5:
        raise ValueError("Số phòng phải trong khoảng 1..5.")
    if guests < 1:
        raise ValueError("Số khách phải lớn hơn 0.")

    hotel = find_hotel(hotel_id)
    room = find_room(hotel, room_type)

    if room.available_rooms < rooms:
        raise ValueError("Không đủ phòng trống.")
    if guests > room.capacity * rooms:
        raise ValueError("Số khách vượt sức chứa phòng đã chọn.")

    total_nights = nights_between(ci, co)
    total_amount = total_nights * room.price_per_night * rooms
    payment = process_payment(total_amount, card_number, cvv)

    if payment["status"] != "success":
        return {
            "status": "payment_failed",
            "hotel_id": hotel.hotel_id,
            "room_type": room.name,
            "reason": payment["reason"],
        }

    booking_code = f"BK-{hotel.hotel_id}-{ci.strftime('%Y%m%d')}-{rooms}"
    return {
        "status": "confirmed",
        "booking_code": booking_code,
        "hotel_id": hotel.hotel_id,
        "hotel_name": hotel.name,
        "room_type": room.name,
        "rooms": rooms,
        "guests": guests,
        "checkin": ci.isoformat(),
        "checkout": co.isoformat(),
        "nights": total_nights,
        "total_amount": total_amount,
        "payment_attempts": payment["attempts"],
    }


def as_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def add_shared_stay_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkin", required=True, help="Ngày checkin (YYYY-MM-DD)")
    parser.add_argument("--checkout", required=True, help="Ngày checkout (YYYY-MM-DD)")
    parser.add_argument("--guests", type=int, required=True, help="Số khách")


def setup_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ứng dụng Python mô phỏng module Hotel (search/filter/booking/payment)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Tìm kiếm khách sạn")
    search.add_argument("--location", required=True, help="Địa điểm, ví dụ: Da Nang")
    add_shared_stay_args(search)
    search.add_argument("--min-price", type=int, default=None, help="Giá tối thiểu")
    search.add_argument("--max-price", type=int, default=None, help="Giá tối đa")
    search.add_argument("--stars", type=int, default=None, help="Số sao")
    search.add_argument("--amenity", default=None, help="Tiện nghi cần có, ví dụ wifi")

    book = sub.add_parser("book", help="Đặt phòng")
    add_shared_stay_args(book)
    book.add_argument("--hotel-id", required=True, help="Mã khách sạn")
    book.add_argument("--room-type", required=True, help="Loại phòng")
    book.add_argument("--rooms", type=int, required=True, help="Số phòng (1..5)")
    book.add_argument("--card-number", required=True, help="Số thẻ")
    book.add_argument("--cvv", required=True, help="CVV 3 chữ số")
    return parser


def _validate_dates_for_search(args: argparse.Namespace) -> None:
    validate_stay_dates(args.checkin, args.checkout)


def main() -> int:
    parser = setup_cli()
    args = parser.parse_args()

    try:
        if args.command == "search":
            _validate_dates_for_search(args)
            if args.guests < 1:
                raise ValueError("Số khách phải lớn hơn 0.")
            hotels = search_hotels(
                location=args.location,
                guests=args.guests,
                min_price=args.min_price,
                max_price=args.max_price,
                stars=args.stars,
                amenity=args.amenity,
            )
            print(as_json({"count": len(hotels), "results": hotels}))
            return 0

        if args.command == "book":
            booking = create_booking(
                hotel_id=args.hotel_id,
                room_type=args.room_type,
                rooms=args.rooms,
                checkin=args.checkin,
                checkout=args.checkout,
                guests=args.guests,
                card_number=args.card_number,
                cvv=args.cvv,
            )
            print(as_json(booking))
            return 0

    except ValueError as exc:
        print(as_json({"error": str(exc)}))
        return 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
