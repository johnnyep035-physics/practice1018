"""
check_db.py
讀取並印出 orders.db 中所有資料表內容以供驗證，並檢驗中文編碼無亂碼。
"""
import sqlite3
import os
import sys
import unicodedata

# 1. 解決 Windows 控制台/IDE 終端機 UTF-8 編碼輸出問題，防止中文出現亂碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

DB_FILE = "orders.db"

def visual_len(text):
    """計算字串在終端機等寬字型下的視覺顯示寬度 (中文字/全形字佔 2 格，英數佔 1 格)"""
    return sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in str(text))

def pad_str(text, width, align='left'):
    """依據視覺顯示寬度對齊字串，解決中文字元排版歪斜問題"""
    text = str(text)
    vl = visual_len(text)
    pad = max(0, width - vl)
    if align == 'right':
        return ' ' * pad + text
    elif align == 'center':
        left = pad // 2
        right = pad - left
        return ' ' * left + text + ' ' * right
    else:
        return text + ' ' * pad

def format_row(values, widths, aligns=None):
    if aligns is None:
        aligns = ['left'] * len(values)
    return " | ".join(pad_str(v, w, a) for v, w, a in zip(values, widths, aligns))

def print_separator(char="=", length=80):
    print(char * length)

def check_database():
    if not os.path.exists(DB_FILE):
        print(f"錯誤：找不到資料庫檔案 {DB_FILE}，請先執行 create_db.py 建立資料庫。")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print_separator("=")
    print("                【 orders.db SQLite 資料庫檢視與編碼驗證 】")
    print_separator("=")

    # 0. 資料庫底層編碼檢測
    cursor.execute("PRAGMA encoding;")
    db_encoding = cursor.fetchone()[0]
    print(f"[*] SQLite 資料庫內建編碼 (PRAGMA encoding): {db_encoding}")
    print(f"[*] Python 終端輸出編碼 (sys.stdout.encoding)  : {sys.stdout.encoding}")
    print_separator("-")

    # 1. 查詢 customer
    print("\n[ 資料表 1: customer (客戶資料表) ]")
    widths = [8, 10, 14, 12, 32]
    headers = ["客戶編號", "客戶名稱", "電話", "建檔日期", "地址"]
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    print(format_row(headers, widths))
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    cursor.execute("SELECT customer_id, name, phone, created_at, address FROM customer")
    customers = cursor.fetchall()
    for row in customers:
        print(format_row(row, widths))
    print(f"-> 總計筆數: {len(customers)} 筆")

    # 2. 查詢 product
    print("\n[ 資料表 2: product (商品資料表) ]")
    widths = [8, 24, 10, 12, 8]
    aligns = ['left', 'left', 'left', 'right', 'right']
    headers = ["商品編號", "商品名稱", "分類", "單價 (NTD)", "庫存"]
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    print(format_row(headers, widths, ['left', 'left', 'left', 'right', 'right']))
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    cursor.execute("SELECT product_id, name, category, price, stock FROM product")
    products = cursor.fetchall()
    for row in products:
        formatted_row = [row[0], row[1], row[2], f"{row[3]:.1f}", row[4]]
        print(format_row(formatted_row, widths, aligns))
    print(f"-> 總計筆數: {len(products)} 筆")

    # 3. 查詢 orders
    print("\n[ 資料表 3: orders (訂單主表) ]")
    widths = [8, 8, 10, 12, 8, 8]
    headers = ["訂單編號", "客戶編號", "客戶名稱", "訂單日期", "狀態", "業務人員"]
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    print(format_row(headers, widths))
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    cursor.execute("""
        SELECT o.order_id, o.customer_id, c.name, o.order_date, o.status, o.sales_rep
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
    """)
    orders = cursor.fetchall()
    for row in orders:
        print(format_row(row, widths))
    print(f"-> 總計筆數: {len(orders)} 筆")

    # 4. 查詢 order_item
    print("\n[ 資料表 4: order_item (訂單明細表 - 複合主鍵: 訂單編號+商品編號) ]")
    widths = [8, 8, 24, 6, 12, 12]
    aligns = ['left', 'left', 'left', 'right', 'right', 'right']
    headers = ["訂單編號", "商品編號", "商品名稱", "數量", "下單單價", "小計金額"]
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    print(format_row(headers, widths, ['left', 'left', 'left', 'right', 'right', 'right']))
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    cursor.execute("""
        SELECT oi.order_id, oi.product_id, p.name, oi.quantity, oi.unit_price, (oi.quantity * oi.unit_price) AS subtotal
        FROM order_item oi
        JOIN product p ON oi.product_id = p.product_id
        ORDER BY oi.order_id, oi.product_id
    """)
    order_items = cursor.fetchall()
    for row in order_items:
        formatted_row = [row[0], row[1], row[2], row[3], f"{row[4]:.1f}", f"{row[5]:.1f}"]
        print(format_row(formatted_row, widths, aligns))
    print(f"-> 總計筆數: {len(order_items)} 筆")

    # 5. 綜合驗證：訂單整合明細與各訂單品項數
    print("\n[ 訂單彙總檢視 (驗證含多項商品之案例) ]")
    widths = [8, 10, 10, 10, 12, 12]
    aligns = ['left', 'left', 'right', 'right', 'right', 'left']
    headers = ["訂單編號", "客戶名稱", "商品種類數", "購買總件數", "訂單總金額", "備註說明"]
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    print(format_row(headers, widths, ['left', 'left', 'right', 'right', 'right', 'left']))
    print_separator("-", sum(widths) + 3 * (len(widths) - 1))
    cursor.execute("""
        SELECT o.order_id, c.name, COUNT(oi.product_id) AS item_count, 
               SUM(oi.quantity) AS total_qty, SUM(oi.quantity * oi.unit_price) AS total_amount
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN order_item oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        ORDER BY o.order_id
    """)
    summary = cursor.fetchall()
    for row in summary:
        note = "★ 含多項商品" if row[2] > 1 else "單一商品"
        formatted_row = [row[0], row[1], row[2], row[3], f"{row[4]:.1f}", note]
        print(format_row(formatted_row, widths, aligns))
    
    # 6. 中文編碼健康度測試
    print("\n[ 中文無亂碼驗證 (Unicode 碼位檢測) ]")
    print_separator("-")
    sample_text = customers[0][1] # "王大明"
    unicode_points = [f"U+{ord(c):04X}" for c in sample_text]
    print(f"取樣文字: '{sample_text}' -> Unicode 編碼: {' '.join(unicode_points)}")
    is_clean = all(ord(c) > 127 and not (0xFFFD == ord(c)) for c in sample_text)
    print(f"驗證結果: {'[PASS] 中文字元標準 UTF-8 編碼正常，無問號或取代字元 (REPLACEMENT CHARACTER)' if is_clean else '[FAIL] 檢測到異常字元'}")
    print_separator("=")

    conn.close()

if __name__ == "__main__":
    check_database()
