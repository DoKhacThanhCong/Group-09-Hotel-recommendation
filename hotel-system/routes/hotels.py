import pandas as pd
import sqlite3

# ---- Đọc dữ liệu CSV ----
csv_file = "hotels.csv"   # Đặt file CSV của bạn cùng thư mục với file Python
df = pd.read_csv(csv_file)

# ---- Kết nối / tạo database ----
conn = sqlite3.connect("hotel.db")
cursor = conn.cursor()

# ---- Tạo bảng (nếu chưa có) ----
cursor.execute("""
CREATE TABLE IF NOT EXISTS hotels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    city TEXT,
    price REAL,
    stars INTEGER,
    rating REAL,
    image_url TEXT,
    buffet BOOLEAN,
    pool BOOLEAN,
    sea BOOLEAN,
    view BOOLEAN,
    review TEXT
)
""")

# ---- Xóa dữ liệu cũ ----
cursor.execute("DELETE FROM hotels")

# ---- Chèn dữ liệu từ CSV vào database ----
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO hotels (name, city, price, stars, rating, image_url, buffet, pool, sea, view, review)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["name"],
        row["city"],
        float(row["price"]),
        int(row["stars"]),
        float(row["rating"]),
        row["image_url"],
        bool(row["buffet"]),
        bool(row["pool"]),
        bool(row["sea"]),
        bool(row["view"]),
        row["review"]
    ))

conn.commit()
conn.close()

print(f" Đã nhập {len(df)} khach san tu '{csv_file}' vao database 'hotel.db'")
