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

## ☁️ 雲端 Render 部署與 CI/CD 自動化管線

本專案已配置完整 **GitHub Actions + Render CI/CD** 自動化流程（定義於 `.github/workflows/deploy.yml`）：

```
[程式碼 Push 到 GitHub]
          │
          ▼
┌───────────────────────────────┐
│  GitHub Actions (CI 階段)     │
│  - Python 3.11 環境安裝       │
│  - 依賴安裝 (pip install)     │
│  - 資料庫初始化與編碼檢驗     │
│  - 執行單元與整合測試 (test)  │
└──────────────┬────────────────┘
               │ 測試通過 (PASS)
               ▼
┌───────────────────────────────┐
│  GitHub Actions (CD 階段)     │
│  - 呼叫 Render Deploy Hook    │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Render 雲端 (自動重新部署)   │
│  - 自動拉取最新通過測試的代碼 │
│  - Gunicorn 服務零停機更新上線│
└───────────────────────────────┘
```

### 如何設定 Render Deploy Hook (只需設定一次)：
1. 登入 [Render](https://render.com) 並進入您的 Web Service 頁面。
2. 點選左側選單 **Settings** &rarr; 找到 **Deploy Hook**。
3. 複製 Deploy Hook 網址（格式如：`https://api.render.com/deploy/srv-xxxxxxx?key=yyyyyyy`）。
4. 前往本專案的 GitHub 倉儲：
   - 點擊 **Settings** &rarr; **Secrets and variables** &rarr; **Actions**。
   - 點擊 **New repository secret**。
   - **Name**: `RENDER_DEPLOY_HOOK_URL`
   - **Secret**: 貼上第 3 步複製的 Deploy Hook 網址，點擊 **Add secret**。
5. 完成！未來每次 push 代碼到 `main` 分支時，GitHub Actions 會自動執行完整測試，只有在測試 100% 通過時，才會觸發 Render 雲端自動上線！

