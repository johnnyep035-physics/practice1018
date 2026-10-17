"""
create_db.py
建立 SQLite 資料庫 orders.db 並插入測試資料
"""
import sqlite3
import os
import sys

# 確保在 Windows 控制台或 IDE 終端機輸出繁體中文不亂碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_FILE = "orders.db"

def init_db():
    # 若舊資料庫存在則先刪除，確保乾淨建立
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"已移除既有 {DB_FILE}，重新建立中...")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 啟用外鍵約束
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. 建立 customer 資料表
    cursor.execute("""
    CREATE TABLE customer (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 2. 建立 product 資料表
    cursor.execute("""
    CREATE TABLE product (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL CHECK (price >= 0),
        stock INTEGER NOT NULL CHECK (stock >= 0),
        category TEXT NOT NULL
    );
    """)

    # 3. 建立 orders 資料表
    cursor.execute("""
    CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        sales_rep TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );
    """)

    # 4. 建立 order_item 資料表 (複合主鍵: order_id + product_id)
    cursor.execute("""
    CREATE TABLE order_item (
        order_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK (quantity > 0),
        unit_price REAL NOT NULL CHECK (unit_price >= 0),
        PRIMARY KEY (order_id, product_id),
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
            ON UPDATE CASCADE
            ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES product(product_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );
    """)

    # 插入 customer 測試資料 (5 筆)
    customers = [
        ("C001", "王大明", "0912-345-678", "台北市中正區忠孝西路一段1號", "2026-01-10"),
        ("C002", "李佳玲", "0923-456-789", "新北市板橋區縣民大道二段7號", "2026-02-15"),
        ("C003", "陳建宏", "0934-567-890", "台中市西屯區台灣大道三段99號", "2026-03-20"),
        ("C004", "林品妤", "0955-667-788", "台南市東區中華東路一段366號", "2026-05-08"),
        ("C005", "張偉碩", "0988-112-233", "高雄市前鎮區中華五路789號", "2026-06-12")
    ]
    cursor.executemany("INSERT INTO customer VALUES (?, ?, ?, ?, ?);", customers)

    # 插入 product 測試資料 (5 筆)
    products = [
        ("P001", "極速人體工學辦公椅", 4500.0, 35, "辦公家具"),
        ("P002", "升降式電動工作桌", 12800.0, 18, "辦公家具"),
        ("P003", "無線降噪全耳罩耳機", 3600.0, 50, "3C周邊"),
        ("P004", "機械式背光鍵盤", 2200.0, 80, "3C周邊"),
        ("P005", "高解析多功能螢幕支架", 1580.0, 42, "電腦配件")
    ]
    cursor.executemany("INSERT INTO product VALUES (?, ?, ?, ?, ?);", products)

    # 插入 orders 測試資料 (5 筆)
    orders_data = [
        ("O001", "C001", "2026-10-01", "已完成", "周伯通"),
        ("O002", "C002", "2026-10-03", "處理中", "郭靖"),
        ("O003", "C003", "2026-10-05", "已出貨", "黃蓉"),
        ("O004", "C004", "2026-10-08", "已出貨", "楊過"),
        ("O005", "C005", "2026-10-12", "待付款", "小龍女")
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?);", orders_data)

    # 插入 order_item 測試資料 (8 筆，包含多項商品案例，並保存下單當時價格)
    # 例如：O001 購買 P001 與 P002 (2項)
    #       O002 購買 P003、P004、P005 (3項，其中 P004 當時促銷特價 2100.0)
    order_items = [
        ("O001", "P001", 2, 4500.0),
        ("O001", "P002", 1, 12800.0),
        ("O002", "P003", 1, 3600.0),
        ("O002", "P004", 2, 2100.0),  # 下單當時優惠價 2100
        ("O002", "P005", 1, 1580.0),
        ("O003", "P001", 1, 4500.0),
        ("O004", "P004", 3, 2200.0),
        ("O005", "P005", 2, 1500.0)   # 下單當時特價 1500
    ]
    cursor.executemany("INSERT INTO order_item VALUES (?, ?, ?, ?);", order_items)

    conn.commit()
    conn.close()
    print("orders.db 資料庫與測試資料建立完成！")

if __name__ == "__main__":
    init_db()
