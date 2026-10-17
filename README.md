# 商業訂單管理系統 (Order Management System)

本專案使用 **Flask + SQLite + Bootstrap 5** 開發，為商業數據分析與訂單管理實作系統，支援繁體中文環境、歷史單價存證、列表直接更新狀態、專屬出貨單與驗收 QR Code 動態生成。

---

## 🌟 核心功能特色

1. **四張核心資料表與約束設計**：
   - `customer`：客戶編號 (PK)、名稱、電話、地址、建檔日期。
   - `product`：商品編號 (PK)、名稱、單價 (CHECK &ge; 0)、庫存 (CHECK &ge; 0)、分類。
   - `orders`：訂單編號 (PK)、客戶編號 (FK)、訂單日期、狀態、業務人員。
   - `order_item`：訂單編號 (FK)、商品編號 (FK)、數量 (CHECK &gt; 0)、下單當時單價 (CHECK &ge; 0)，以**「訂單編號 + 商品編號」為複合主鍵**。
2. **管理員認證與維護**：
   - 內建安全雜湊密碼驗證與 Session 管理。
   - 登入後可維護客戶、商品規格/庫存、訂單總覽。
3. **新增訂單多品項選購**：
   - 客戶使用**下拉選單**指定。
   - 商品支援**一次勾選多項並填寫數量**，前端即時試算總金額，具備庫存即時防呆。
4. **歷史交易單價快照存證**：
   - 下單時保存當下單價於 `order_item.unit_price`，後續商品調價不影響歷史訂單記錄。
5. **訂單狀態直接在列表更新**：
   - 訂單狀態（處理中 / 已出貨 / 已完成 / 已取消）可在列表下拉選單直接切換，透過 AJAX 即時存檔並彈出 Toast 提示。
6. **專屬訂單頁面與出貨單 QR Code**：
   - 專屬頁面 `/order/<訂單編號>`，呈現完整出貨明細憑單。
   - 自動生成專屬 Base64 QR Code，並支援一鍵列印 (`window.print()`)。
7. **完整 5 筆繁體中文測試資料**：
   - 涵蓋含多項商品訂單（例如 O001 購買 2 款商品、O002 購買 3 款商品與促銷特價案例）。

---

## 🚀 快速啟動方式

### 1. 安裝相依套件
```bash
pip install -r requirements.txt
```

### 2. 啟動 Web 服務
```bash
python app.py
```
- 瀏覽器開啟：`http://127.0.0.1:5000`
- **預設管理員帳號**：`admin`
- **預設管理員密碼**：`admin123`

---

## 🔍 資料庫與自動化驗證

1. **終端資料庫內容與編碼檢視**：
   ```bash
   python check_db.py
   ```
2. **執行整合單元測試**：
   ```bash
   python test_app.py
   ```
3. **還原初始測試資料庫**：
   ```bash
   python database.py
   ```

---

## ☁️ 雲端 Render 部署說明

本專案支援一鍵部署至 [Render.com](https://render.com) 免費 Web Service：
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
