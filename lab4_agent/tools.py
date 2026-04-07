from langchain_core.tools import tool

# ================= MOCK DATA =================

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "price_per_night": 3500000, "rating": 4.4},
        {"name": "Lahana Resort", "price_per_night": 800000, "rating": 4.0},
        {"name": "9Station Hostel", "price_per_night": 200000, "rating": 4.5},
    ],
    "Đà Nẵng": [
        {"name": "Vinpearl Resort", "price_per_night": 3500000, "rating": 4.4},
        {"name": "Lahana Resort", "price_per_night": 800000, "rating": 4.0},
        {"name": "9Station Hostel", "price_per_night": 200000, "rating": 4.5},
    ]
    
}

# ================= HELPER =================

def format_price(price):
    return f"{price:,}".replace(",", ".") + "đ"

# ================= TOOL 1 =================

@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.
    Tham số:
    - origin (str): Thành phố khởi hành (ví dụ: "Hà Nội", "Hồ Chí Minh")
    - destination (str): Thành phố điểm đến (ví dụ: "Đà Nẵng", "Phú Quốc")
    Trả về danh sách các chuyến bay, bao gồm: Hãng bay, Giờ khởi hành, Giá vé
    Nếu không tìm thấy chuyến bay phù hợp,trả về thông báo: "Không có chuyến bay."
    """
    flights = FLIGHTS_DB.get((origin, destination))

    if not flights:
        flights = FLIGHTS_DB.get((destination, origin))

    if not flights:
        return f"Không tìm thấy chuyến bay từ {origin} đến {destination}"

    result = "Danh sách chuyến bay:\n"

    for f in flights:
        result += (
            f"- {f['airline']} | {f['departure']} → {f['arrival']} | "
            f"{format_price(f['price'])}\n"
        )

    return result

# ================= TOOL 2 =================

@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo mức giá tối đa mỗi đêm.
    Tham số:
    - city (str): Tên thành phố (ví dụ: "Đà Nẵng", "Phú Quốc", "Hồ Chí Minh")
    - max_price_per_night (int, optional): Giá tối đa mỗi đêm (đơn vị: VND), mặc định không giới hạn giá.
    Trả về danh sách các khách sạn phù hợp, bao gồm:Tên khách sạn, Số sao, Giá mỗi đêm, Khu vực, Đánh giá (rating)
    """
    hotels = HOTELS_DB.get(city)

    if not hotels:
        return f"Không có dữ liệu khách sạn tại {city}"

    filtered = [h for h in hotels if h["price_per_night"] <= max_price_per_night]

    if not filtered:
        return f"Không tìm thấy khách sạn dưới {format_price(max_price_per_night)}"

    filtered.sort(key=lambda x: x["rating"], reverse=True)

    result = "Khách sạn gợi ý:\n"

    for h in filtered:
        result += (
            f"- {h['name']} | {format_price(h['price_per_night'])}/đêm | ⭐ {h['rating']}\n"
        )

    return result

# ================= TOOL 3 =================

@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính toán ngân sách còn lại sau khi trừ các khoản chi phí.

    Tham số:
    - total_budget (int): Tổng ngân sách ban đầu (đơn vị: VND)
    - expenses (str): Chuỗi mô tả các khoản chi, mỗi khoản cách nhau bằng dấu phẩy.
    Định dạng: "tên_khoản:số_tiền" (ví dụ: "ve_may_bay:890000,khach_san:650000")
    Trả về bảng chi tiết các khoản chi. Đồng thời trả về số tiền còn lại sau khi trừ chi phí.
    Nếu tổng chi vượt quá ngân sách,cảnh báo rõ ràng số tiền thiếu.
    """
    try:
        items = expenses.split(",")

        total = 0
        result = "Bảng chi phí:\n"

        for item in items:
            name, value = item.split(":")
            value = int(value)

            total += value
            result += f"- {name}: {format_price(value)}\n"

        remaining = total_budget - total

        result += "\n---\n"
        result += f"Tổng chi: {format_price(total)}\n"
        result += f"Ngân sách: {format_price(total_budget)}\n"
        result += f"Còn lại: {format_price(remaining)}\n"

        if remaining < 0:
            result += "⚠️ Vượt ngân sách!"

        return result

    except:
        return "Sai format. Ví dụ đúng: ve:1000000,khach_san:500000"