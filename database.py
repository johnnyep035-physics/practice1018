"""
database.py
SQLite 資料庫操作模組：包含資料表建立、外鍵支援、預設測試資料初始化。
"""
import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

# 確保在 Windows 控制台輸出中文不亂碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.db")

def get_db():
    """獲取支援 Row 物件與外鍵約束的 SQLite 連線"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(force_recreate=False):
    """初始化資料庫架構與預設測試資料"""
    if force_recreate and os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
            print(f"[DB] 已移除既有 {DB_FILE}，進行乾淨重建。")
        except Exception as e:
            print(f"[DB] 移除既有資料庫時提示: {e}")

    conn = get_db()
    cursor = conn.cursor()

    # 1. 客戶資料表 customer (客戶編號 PK、名稱、電話、地址)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
    """)

    # 2. 商品資料表 product (商品編號 PK、名稱、單價、庫存、分類)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL CHECK (price >= 0),
        stock INTEGER NOT NULL CHECK (stock >= 0),
        category TEXT NOT NULL
    );
    """)

    # 3. 訂單主表 orders (訂單編號 PK、客戶編號 FK、訂單日期、狀態、業務人員)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('處理中', '已出貨', '已完成', '已取消')),
        sales_rep TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT
    );
    """)

    # 4. 訂單明細表 order_item (訂單編號 FK、商品編號 FK、數量、單價)，以「訂單編號 + 商品編號」為複合主鍵
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_item (
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

    # 5. 管理員使用者表 admin_user
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_user (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        display_name TEXT NOT NULL,
        role TEXT DEFAULT 'admin'
    );
    """)

    # 檢查是否已有管理員，無則插入預設管理員
    cursor.execute("SELECT COUNT(*) FROM admin_user;")
    if cursor.fetchone()[0] == 0:
        default_pwd_hash = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO admin_user (username, password_hash, display_name) VALUES (?, ?, ?);",
            ("admin", default_pwd_hash, "系統管理員")
        )
        print("[DB] 已建立預設管理員: 帳號 admin / 密碼 admin123")

    # 檢查 customer 是否需要插入 5 筆測試資料
    cursor.execute("SELECT COUNT(*) FROM customer;")
    if cursor.fetchone()[0] == 0:
        customers = [
            ("C001", "王大明", "0912-345-678", "台北市中正區忠孝西路一段1號", "2026-01-10"),
            ("C002", "李佳玲", "0923-456-789", "新北市板橋區縣民大道二段7號", "2026-02-15"),
            ("C003", "陳建宏", "0934-567-890", "台中市西屯區台灣大道三段99號", "2026-03-20"),
            ("C004", "林品妤", "0955-667-788", "台南市東區中華東路一段366號", "2026-05-08"),
            ("C005", "張偉碩", "0988-112-233", "高雄市前鎮區中華五路789號", "2026-06-12")
        ]
        cursor.executemany("INSERT INTO customer (customer_id, name, phone, address, created_at) VALUES (?, ?, ?, ?, ?);", customers)
        print("[DB] 已寫入 5 筆客戶測試資料")

    # 檢查 product 是否需要插入 5 筆測試資料
    cursor.execute("SELECT COUNT(*) FROM product;")
    if cursor.fetchone()[0] == 0:
        products = [
            ("P001", "極速人體工學辦公椅", 4500.0, 35, "辦公家具"),
            ("P002", "升降式電動工作桌", 12800.0, 18, "辦公家具"),
            ("P003", "無線降噪全耳罩耳機", 3600.0, 50, "3C周邊"),
            ("P004", "機械式背光鍵盤", 2200.0, 80, "3C周邊"),
            ("P005", "高解析多功能螢幕支架", 1580.0, 42, "電腦配件")
        ]
        cursor.executemany("INSERT INTO product (product_id, name, price, stock, category) VALUES (?, ?, ?, ?, ?);", products)
        print("[DB] 已寫入 5 筆商品測試資料")

    # 檢查 orders 是否需要插入 5 筆測試資料
    cursor.execute("SELECT COUNT(*) FROM orders;")
    if cursor.fetchone()[0] == 0:
        orders_data = [
            ("O001", "C001", "2026-10-01", "已完成", "周伯通"),
            ("O002", "C002", "2026-10-03", "處理中", "郭靖"),
            ("O003", "C003", "2026-10-05", "已出貨", "黃蓉"),
            ("O004", "C004", "2026-10-08", "已出貨", "楊過"),
            ("O005", "C005", "2026-10-12", "處理中", "小龍女")
        ]
        cursor.executemany("INSERT INTO orders (order_id, customer_id, order_date, status, sales_rep) VALUES (?, ?, ?, ?, ?);", orders_data)
        print("[DB] 已寫入 5 筆訂單測試資料")

    # 檢查 order_item 是否需要插入測試資料 (含多項商品案例，並保存下單當時價格)
    cursor.execute("SELECT COUNT(*) FROM order_item;")
    if cursor.fetchone()[0] == 0:
        order_items = [
            ("O001", "P001", 2, 4500.0),
            ("O001", "P002", 1, 12800.0), # 多項商品
            ("O002", "P003", 1, 3600.0),
            ("O002", "P004", 2, 2100.0),  # 下單當時促銷價 2100 (現價 2200)
            ("O002", "P005", 1, 1580.0),  # 多項商品 (3項)
            ("O003", "P001", 1, 4500.0),
            ("O004", "P004", 3, 2200.0),
            ("O005", "P005", 2, 1500.0)   # 下單當時特價 1500 (現價 1580)
        ]
        cursor.executemany("INSERT INTO order_item (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?);", order_items)
        print("[DB] 已寫入訂單明細測試資料 (包含含多項商品之案例與歷史單價)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db(force_recreate=True)
