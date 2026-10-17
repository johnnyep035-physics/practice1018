"""
app.py
訂單管理系統 (Flask + SQLite + Bootstrap 5) 主應用程式
"""
import os
import sys
import io
import base64
from datetime import datetime
from functools import wraps
import qrcode
from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
)
from werkzeug.security import check_password_hash
from database import get_db, init_db

# 解決 Windows 控制台中文輸出編碼問題
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "order_management_secret_key_2026")

# 確保資料庫與初始測試資料備妥
init_db(force_recreate=False)

def login_required(f):
    """登入驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("請先登入系統以存取管理功能", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- 認證路由 -----------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin_user WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['role'] = user['role']
            flash(f"歡迎回來，{user['display_name']}！", "success")
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            flash("帳號或密碼錯誤，請重新輸入 (預設帳號: admin / 密碼: admin123)", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("您已安全登出系統", "info")
    return redirect(url_for('login'))

# ----------------- 儀表板首頁 -----------------

@app.route('/')
@login_required
def index():
    conn = get_db()
    cursor = conn.cursor()

    # 統計數據
    cursor.execute("SELECT COUNT(*) FROM customer")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM product")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity * unit_price) FROM order_item")
    total_revenue = cursor.fetchone()[0] or 0.0

    # 庫存警示 (庫存小於 20 的商品)
    cursor.execute("SELECT * FROM product WHERE stock < 25 ORDER BY stock ASC")
    low_stock_products = cursor.fetchall()

    # 最近 5 筆訂單
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.status, o.sales_rep, c.name AS customer_name,
               COUNT(oi.product_id) AS item_count,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_amount
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        LEFT JOIN order_item oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        ORDER BY o.order_date DESC, o.order_id DESC
        LIMIT 5
    """)
    recent_orders = cursor.fetchall()
    conn.close()

    return render_template(
        'index.html',
        total_customers=total_customers,
        total_products=total_products,
        total_orders=total_orders,
        total_revenue=total_revenue,
        low_stock_products=low_stock_products,
        recent_orders=recent_orders
    )

# ----------------- 客戶管理 -----------------

@app.route('/customers')
@login_required
def customers_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(o.order_id) AS order_count
        FROM customer c
        LEFT JOIN orders o ON c.customer_id = o.customer_id
        GROUP BY c.customer_id
        ORDER BY c.customer_id ASC
    """)
    customers = cursor.fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)

@app.route('/customers/add', methods=['POST'])
@login_required
def customer_add():
    customer_id = request.form.get('customer_id', '').strip()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    if not customer_id or not name or not phone or not address:
        flash("請完整填寫所有客戶欄位", "danger")
        return redirect(url_for('customers_list'))

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customer (customer_id, name, phone, address, created_at) VALUES (?, ?, ?, ?, ?)",
            (customer_id, name, phone, address, datetime.now().strftime("%Y-%m-%d"))
        )
        conn.commit()
        flash(f"客戶 [{customer_id} - {name}] 新增成功！", "success")
    except sqlite3.IntegrityError:
        flash(f"客戶編號 {customer_id} 已存在，請使用不同編號", "danger")
    finally:
        conn.close()

    return redirect(url_for('customers_list'))

@app.route('/customers/edit/<customer_id>', methods=['POST'])
@login_required
def customer_edit(customer_id):
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()

    if not name or not phone or not address:
        flash("請完整填寫客戶資訊", "danger")
        return redirect(url_for('customers_list'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE customer SET name = ?, phone = ?, address = ? WHERE customer_id = ?",
        (name, phone, address, customer_id)
    )
    conn.commit()
    conn.close()
    flash(f"客戶 [{customer_id}] 資料更新成功！", "success")
    return redirect(url_for('customers_list'))

@app.route('/customers/delete/<customer_id>', methods=['POST'])
@login_required
def customer_delete(customer_id):
    conn = get_db()
    cursor = conn.cursor()
    # 檢查是否有關聯訂單
    cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = ?", (customer_id,))
    order_count = cursor.fetchone()[0]

    if order_count > 0:
        flash(f"無法刪除客戶 [{customer_id}]，因為該客戶名下已有 {order_count} 筆歷史訂單。", "warning")
    else:
        cursor.execute("DELETE FROM customer WHERE customer_id = ?", (customer_id,))
        conn.commit()
        flash(f"客戶 [{customer_id}] 已成功刪除", "success")
    conn.close()
    return redirect(url_for('customers_list'))

# ----------------- 商品管理 -----------------

@app.route('/products')
@login_required
def products_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product ORDER BY product_id ASC")
    products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products/add', methods=['POST'])
@login_required
def product_add():
    product_id = request.form.get('product_id', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    try:
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
    except ValueError:
        flash("單價或庫存格式不正確", "danger")
        return redirect(url_for('products_list'))

    if price < 0 or stock < 0:
        flash("單價與庫存不可為負數 (CHECK 約束)", "danger")
        return redirect(url_for('products_list'))

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO product (product_id, name, price, stock, category) VALUES (?, ?, ?, ?, ?)",
            (product_id, name, price, stock, category)
        )
        conn.commit()
        flash(f"商品 [{product_id} - {name}] 新增成功！", "success")
    except sqlite3.IntegrityError:
        flash(f"商品編號 {product_id} 已存在，請使用不同編號", "danger")
    finally:
        conn.close()

    return redirect(url_for('products_list'))

@app.route('/products/edit/<product_id>', methods=['POST'])
@login_required
def product_edit(product_id):
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    try:
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
    except ValueError:
        flash("單價或庫存格式不正確", "danger")
        return redirect(url_for('products_list'))

    if price < 0 or stock < 0:
        flash("單價與庫存不可為負數", "danger")
        return redirect(url_for('products_list'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE product SET name = ?, price = ?, stock = ?, category = ? WHERE product_id = ?",
        (name, price, stock, category, product_id)
    )
    conn.commit()
    conn.close()
    flash(f"商品 [{product_id}] 資料更新成功！注意：商品改價僅適用於未來新訂單，歷史訂單單價不受影響。", "info")
    return redirect(url_for('products_list'))

@app.route('/products/delete/<product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM order_item WHERE product_id = ?", (product_id,))
    item_count = cursor.fetchone()[0]

    if item_count > 0:
        flash(f"無法刪除商品 [{product_id}]，因為已有訂單包含此項商品。", "warning")
    else:
        cursor.execute("DELETE FROM product WHERE product_id = ?", (product_id,))
        conn.commit()
        flash(f"商品 [{product_id}] 已成功刪除", "success")
    conn.close()
    return redirect(url_for('products_list'))

# ----------------- 訂單管理 -----------------

@app.route('/orders')
@login_required
def orders_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.order_id, o.customer_id, c.name AS customer_name, c.phone AS customer_phone,
               o.order_date, o.status, o.sales_rep,
               COUNT(oi.product_id) AS item_count,
               COALESCE(SUM(oi.quantity), 0) AS total_qty,
               COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_amount
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        LEFT JOIN order_item oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        ORDER BY o.order_date DESC, o.order_id DESC
    """)
    orders = cursor.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
def order_new():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        order_id = request.form.get('order_id', '').strip()
        customer_id = request.form.get('customer_id', '').strip()
        order_date = request.form.get('order_date', '').strip() or datetime.now().strftime("%Y-%m-%d")
        status = request.form.get('status', '處理中')
        sales_rep = request.form.get('sales_rep', '').strip() or session.get('display_name', '業務專員')

        # 獲取勾選的商品清單
        selected_product_ids = request.form.getlist('selected_products')

        if not order_id:
            flash("請填寫訂單編號", "danger")
            conn.close()
            return redirect(url_for('order_new'))

        if not customer_id:
            flash("請選擇客戶", "danger")
            conn.close()
            return redirect(url_for('order_new'))

        if not selected_product_ids:
            flash("請至少勾選一項商品以建立訂單", "warning")
            conn.close()
            return redirect(url_for('order_new'))

        # 驗證各商品數量並檢查庫存
        order_items_to_insert = []
        for pid in selected_product_ids:
            qty_str = request.form.get(f'quantity_{pid}', '1')
            try:
                qty = int(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                flash(f"商品 [{pid}] 的數量必須為大於 0 的整數", "danger")
                conn.close()
                return redirect(url_for('order_new'))

            # 查詢當前商品的即時單價與庫存
            cursor.execute("SELECT name, price, stock FROM product WHERE product_id = ?", (pid,))
            prod = cursor.fetchone()
            if not prod:
                flash(f"找不到商品編號 {pid}", "danger")
                conn.close()
                return redirect(url_for('order_new'))

            if qty > prod['stock']:
                flash(f"商品 [{prod['name']}] 庫存不足 (現有庫存: {prod['stock']}，欲購買: {qty})", "danger")
                conn.close()
                return redirect(url_for('order_new'))

            # 保存「下單當下的單價」
            current_unit_price = prod['price']
            order_items_to_insert.append((pid, qty, current_unit_price))

        try:
            # 1. 寫入 orders 主表
            cursor.execute(
                "INSERT INTO orders (order_id, customer_id, order_date, status, sales_rep) VALUES (?, ?, ?, ?, ?)",
                (order_id, customer_id, order_date, status, sales_rep)
            )

            # 2. 寫入 order_item 明細表並扣除商品庫存
            for pid, qty, unit_price in order_items_to_insert:
                cursor.execute(
                    "INSERT INTO order_item (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (order_id, pid, qty, unit_price)
                )
                cursor.execute(
                    "UPDATE product SET stock = stock - ? WHERE product_id = ?",
                    (qty, pid)
                )

            conn.commit()
            flash(f"訂單 [{order_id}] 建立成功！商品已依下單當時單價儲存，庫存已同步扣減。", "success")
            return redirect(url_for('order_detail', order_id=order_id))

        except sqlite3.IntegrityError as e:
            conn.rollback()
            flash(f"建立訂單失敗：訂單編號 {order_id} 可能已重複或違反約束。錯誤細節: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for('order_new'))

    # GET 請求：加載客戶下拉選單與商品列表
    cursor.execute("SELECT customer_id, name, phone, address FROM customer ORDER BY customer_id ASC")
    customers = cursor.fetchall()

    cursor.execute("SELECT product_id, name, price, stock, category FROM product ORDER BY category, product_id")
    products = cursor.fetchall()

    # 自動預設下一筆訂單編號
    cursor.execute("SELECT order_id FROM orders ORDER BY order_id DESC LIMIT 1")
    last_order = cursor.fetchone()
    if last_order and last_order[0].startswith('O') and last_order[0][1:].isdigit():
        next_order_num = int(last_order[0][1:]) + 1
        suggested_order_id = f"O{next_order_num:03d}"
    else:
        suggested_order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M')}"

    conn.close()
    return render_template(
        'order_new.html',
        customers=customers,
        products=products,
        today=datetime.now().strftime("%Y-%m-%d"),
        suggested_order_id=suggested_order_id
    )

# 狀態直接在訂單列表更新 (支援 AJAX 與傳統 POST)
@app.route('/api/orders/<order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if request.is_json:
        data = request.get_json()
        new_status = data.get('status', '').strip()
    else:
        new_status = request.form.get('status', '').strip()

    valid_statuses = ['處理中', '已出貨', '已完成', '已取消']
    if new_status not in valid_statuses:
        if request.is_json:
            return jsonify({'success': False, 'message': '無效的訂單狀態'}), 400
        flash("無效的訂單狀態", "danger")
        return redirect(url_for('orders_list'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status, order_id))
    conn.commit()
    conn.close()

    if request.is_json:
        return jsonify({
            'success': True,
            'message': f"訂單 [{order_id}] 狀態已更新為【{new_status}】",
            'order_id': order_id,
            'new_status': new_status
        })

    flash(f"訂單 [{order_id}] 狀態已更新為【{new_status}】", "success")
    return redirect(url_for('orders_list'))

@app.route('/orders/delete/<order_id>', methods=['POST'])
@login_required
def order_delete(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
    flash(f"訂單 [{order_id}] 及其明細已成功刪除", "success")
    return redirect(url_for('orders_list'))

# ----------------- 專屬訂單頁面與出貨單 QRCode -----------------

@app.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    conn = get_db()
    cursor = conn.cursor()

    # 查詢訂單與客戶資訊
    cursor.execute("""
        SELECT o.order_id, o.order_date, o.status, o.sales_rep,
               c.customer_id, c.name AS customer_name, c.phone AS customer_phone, c.address AS customer_address
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        WHERE o.order_id = ?
    """, (order_id,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash(f"找不到訂單編號 {order_id}", "danger")
        return redirect(url_for('orders_list'))

    # 查詢訂單明細，同時撈取商品目前的現價 (current_price)，比對顯示下單當時保存之單價
    cursor.execute("""
        SELECT oi.order_id, oi.product_id, oi.quantity, oi.unit_price AS order_unit_price,
               p.name AS product_name, p.category AS product_category, p.price AS current_product_price,
               (oi.quantity * oi.unit_price) AS subtotal
        FROM order_item oi
        JOIN product p ON oi.product_id = p.product_id
        WHERE oi.order_id = ?
        ORDER BY oi.product_id ASC
    """, (order_id,))
    items = cursor.fetchall()
    conn.close()

    total_amount = sum(item['subtotal'] for item in items)
    total_qty = sum(item['quantity'] for item in items)

    # 產生出貨單 QRCode
    # QRCode 內含出貨單專屬網址與核驗摘要
    qr_data = request.host_url.rstrip('/') + url_for('order_detail', order_id=order_id)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e293b", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template(
        'order_detail.html',
        order=order,
        items=items,
        total_amount=total_amount,
        total_qty=total_qty,
        qr_b64=qr_b64,
        qr_url=qr_data
    )

if __name__ == '__main__':
    # 支援本地執行與雲端 PORT 環境變數動態綁定
    port = int(os.environ.get("PORT", 5000))
    print("[Flask] 訂單管理系統啟動中...")
    print(f"[Flask] 請在瀏覽器開啟: http://127.0.0.1:{port}")
    print("[Flask] 管理員預設帳號: admin / 密碼: admin123")
    app.run(host='0.0.0.0', port=port, debug=False)

