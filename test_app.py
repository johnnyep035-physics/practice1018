"""
test_app.py
端對端測試腳本：驗證 Flask 應用程式之認證、CRUD、歷史單價存證、狀態切換與 QRCode 生成。
"""
import sys
import unittest
from app import app
from database import init_db, get_db

# 解決 Windows 控制台輸出中文不亂碼
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

class OrderSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db(force_recreate=True)

    def test_01_login(self):
        # 測試錯誤密碼
        res = self.client.post('/login', data={'username': 'admin', 'password': 'wrongpassword'}, follow_redirects=True)
        self.assertIn('帳號或密碼錯誤'.encode('utf-8'), res.data)

        # 測試正確登入
        res = self.client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertIn('營運儀表板總覽'.encode('utf-8'), res.data)
        print("[TEST 1/6 PASS] 管理員帳密登入與驗證成功")

    def test_02_dashboard_and_lists(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        res_cust = self.client.get('/customers')
        self.assertIn('王大明'.encode('utf-8'), res_cust.data)

        res_prod = self.client.get('/products')
        self.assertIn('極速人體工學辦公椅'.encode('utf-8'), res_prod.data)

        res_orders = self.client.get('/orders')
        self.assertIn('O001'.encode('utf-8'), res_orders.data)
        print("[TEST 2/6 PASS] 儀表板、客戶列表、商品列表、訂單列表展示正常 (繁中無亂碼)")

    def test_03_create_multi_item_order(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        # 新增一筆含 2 項商品的訂單 O006
        form_data = {
            'order_id': 'O006',
            'customer_id': 'C001',
            'order_date': '2026-10-18',
            'sales_rep': '周伯通',
            'status': '處理中',
            'selected_products': ['P001', 'P003'],
            'quantity_P001': '2',
            'quantity_P003': '3'
        }
        res = self.client.post('/orders/new', data=form_data, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 驗證資料庫中的 order_item 是否存入當下單價 (P001: 4500, P003: 3600)
        conn = get_db()
        items = conn.execute("SELECT product_id, quantity, unit_price FROM order_item WHERE order_id = 'O006' ORDER BY product_id").fetchall()
        conn.close()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['unit_price'], 4500.0)
        self.assertEqual(items[1]['unit_price'], 3600.0)
        print("[TEST 3/6 PASS] 多品項勾選新增訂單成功，並正確保存下單當時單價")

    def test_04_historical_price_preservation(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        # 修改 P001 商品價格從 4500 調漲為 5200
        res = self.client.post('/products/edit/P001', data={
            'name': '極速人體工學辦公椅(升級版)',
            'price': '5200.0',
            'stock': '30',
            'category': '辦公家具'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 檢驗歷史訂單 O001 中的 P001 單價是否仍為 4500.0，不受商品改價影響
        conn = get_db()
        hist_item = conn.execute("SELECT unit_price FROM order_item WHERE order_id = 'O001' AND product_id = 'P001'").fetchone()
        current_prod = conn.execute("SELECT price FROM product WHERE product_id = 'P001'").fetchone()
        conn.close()

        self.assertEqual(hist_item['unit_price'], 4500.0)
        self.assertEqual(current_prod['price'], 5200.0)
        print("[TEST 4/6 PASS] 商品調價驗證：商品價格調為 5200，歷史訂單保存之單價仍為 4500，歷史單價不受影響！")

    def test_05_inline_status_update(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        # 透過 AJAX 更新訂單狀態至 '已出貨'
        res = self.client.post('/api/orders/O002/status', json={'status': '已出貨'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])

        conn = get_db()
        status = conn.execute("SELECT status FROM orders WHERE order_id = 'O002'").fetchone()[0]
        conn.close()
        self.assertEqual(status, '已出貨')
        print("[TEST 5/6 PASS] 列表即時更新訂單狀態 API 執行成功")

    def test_06_order_page_and_qrcode(self):
        self.client.post('/login', data={'username': 'admin', 'password': 'admin123'})
        res = self.client.get('/order/O001')
        self.assertEqual(res.status_code, 200)
        self.assertIn('出貨明細憑單'.encode('utf-8'), res.data)
        self.assertIn('data:image/png;base64,'.encode('utf-8'), res.data) # 確認 QRCode 圖片生成
        print("[TEST 6/6 PASS] 專屬訂單頁面 /order/<id> 與出貨單 QRCode 生成成功！")

if __name__ == '__main__':
    unittest.main()
