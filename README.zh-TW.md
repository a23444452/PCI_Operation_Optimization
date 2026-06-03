# PCI Operation Optimization

全端 Web 應用程式，用於 PCI（製程控制檢驗）作業優化。管理 crate 卸載判定、出貨假設、COA（品質證書）、每日分析儀表板、風險管理及組態資料維護。

## 技術架構

**前端：** React 19, Vite, TypeScript, TailwindCSS 4, Radix UI, ECharts, TanStack Query/Table

**後端：** FastAPI, SQLAlchemy, Alembic, APScheduler, PostgreSQL

**認證：** Azure AD SSO + LDAP + JWT

## 系統需求

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+（使用 port 5433）
- Corning AD 網域存取權限（ap.corning.com）
- Oracle PPDA、MESDW SQL Server、SSAS Cube 的網路連線（ETL 用）

## 快速啟動

### 1. PostgreSQL

建立資料庫：
```sql
CREATE DATABASE pci_optimization;
```

### 2. 後端

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows

pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env，填入資料庫連線及 Azure AD 設定

# 執行資料庫遷移
alembic upgrade head

# 匯入初始資料（廠區、槽體、項目、管理員帳號）
python -m app.seed

# 啟動伺服器
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. 前端

```bash
cd frontend
npm install

# 設定環境變數
cp .env.example .env
# 編輯 .env，填入 Azure AD Client ID 和 Tenant ID

# 啟動開發伺服器
npm run dev
```

開啟瀏覽器：http://localhost:8080

## 預設帳號

- **管理員：** admin / admin123
- **SSO：** 使用 Corning Azure AD 帳號（需為 PCI-Optimization-Access AD 群組成員）

---

## 功能模組

### 1. PCI Offload（卸載判定）

**用途：** 依據缺陷標準評估 crate，決定是否卸載（退貨）或放行。

**業務邏輯：**
- 每個廠區定義缺陷判定標準（例如：Blister > 100um、Platinum > 50um、Crystalline Pt > 40um）
- 系統從 Oracle PPDA 擷取缺陷檢驗數據，計算每個 crate 的缺陷比率
- 超過任一標準門檻的 crate 標記為不合格
- 操作員選擇要卸載的 crate；選擇不合格品需要 `offload_override` 權限

**操作步驟：**
1. 從下拉選單選擇廠區
2. 檢視 crate 列表 — 每行顯示缺陷比率及合規狀態
3. 綠色指標 = 合格；紅色 = 超標
4. 勾選要卸載的 crate，點擊「確認選擇」
5. 若選擇不合格品，系統會要求填寫覆核理由（需權限）

**主要缺陷類型：**
| 代碼 | 名稱 | 說明 |
|------|------|------|
| 1 | Blister | 玻璃內氣泡 |
| 3 | Platinum | 鉑金顆粒夾雜物 |
| 5 | Surface Blister | 表面氣泡 |
| 6 | Needle Pt | 針狀鉑金 |
| 7 | Crystalline Pt | 結晶鉑金夾雜物 |

---

### 2. Shipping Assumption（出貨假設）

**用途：** 使用 FIFO（先進先出）邏輯將 crate 分配至出貨排程。

**業務邏輯：**
- 出貨排程定義目標出貨日期及需求數量
- FIFO 截止規則：`cut_lot_end_date ≤ (ship_date - 3 天)`
  - 只有切割完成日在出貨日前至少 3 天的 crate 才符合資格
- 符合資格的 crate 依 `cut_lot_end_date` 升序排列（最舊的優先）
- 系統依序分配 crate 直到滿足需求數量

**操作步驟：**
1. 檢視所有出貨排程及其滿足狀態
2. 點擊排程展開，查看已分配的 crate
3. 進度條顯示滿足百分比
4. 點擊「重新計算」重跑 FIFO 分配（例如新 crate 入庫後）
5. 匯出分配結果供物流協調使用

**FIFO 範例：**
```
出貨日期：2026-06-10
截止日期：2026-06-07（ship_date - 3 天）

符合資格的 crate（cut_lot_end_date ≤ 2026-06-07）：
  Crate A：切割完成 2026-06-01 ✓（優先分配）
  Crate B：切割完成 2026-06-05 ✓（第二分配）
  Crate C：切割完成 2026-06-08 ✗（太新，不符資格）
```

---

### 3. COA（品質證書）

**用途：** 產生 COA 報告，結合缺陷比率及 MSL（機械應力等級）數據。

**業務邏輯：**
- 缺陷數據來自 Oracle PPDA（透過 ETL）
- MSL 數據來自 SSAS Cube（透過 ETL）
- COA 將兩者整合為每個 crate 的統一品質報告
- 支援 Excel 匯出供客戶交付

**操作步驟：**
1. 依日期範圍及廠區篩選
2. 在表格中檢視合併的缺陷 + MSL 數據
3. 欄位包含：crate ID、Gen、所有缺陷比率、MSL 指標、複合分數
4. 點擊「匯出 Excel」下載格式化的 COA 試算表

**複合欄位：**
- `NG(Pt_CPt_SD)<6%` — Blister、Other、SBL、Needle Pt、Pt、Crystalline Pt 的加總（須 < 6%）
- `ADG` — A 面及 B 面附著玻璃的加總

**MSL 欄位：**
- A-Crack, A-Drip, A-ADG, A-SC, A-Stain
- B-Drip, B-Stain, B-SC, B-Crack, B-ADG
- Full Sheet Broken

---

### 4. Daily Analysis（每日分析）

**用途：** 以堆疊長條圖視覺化品質趨勢，依槽體分組。

三個子標籤：

#### 4a. ML（熔融損失）

追蹤每個槽體隨時間的熔融相關缺陷指標。

#### 4b. MSL（機械應力等級）

追蹤 SSAS Cube 數據中每個槽體的機械應力指標。

#### 4c. Attribute（屬性）

追蹤每個槽體隨時間的屬性級品質指標。

**圖表格式：**
- 每個槽體一張堆疊長條圖
- X 軸：日期
- Y 軸：缺陷損失百分比
- 每個堆疊區段代表一個 crate 對當日總量的貢獻
- 滑鼠懸停可查看個別 crate 詳情

**操作步驟：**
1. 選擇子標籤（ML / MSL / Attribute）
2. 選擇日期範圍（預設：過去 30 天）
3. 圖表自動填入所有活躍槽體
4. 點擊長條區段可下鑽至 crate 詳情

---

### 5. Risk Management（風險管理）

**用途：** 依可設定的規則標記高風險 crate，追蹤風險等級。

**風險等級：**
- **High**（紅色）— 需立即處理
- **Medium**（黃色）— 密切監控
- **Low**（綠色）— 僅供參考

**操作步驟：**
1. 依等級分組檢視風險 crate
2. 使用等級按鈕篩選
3. 點擊 crate 查看觸發的規則
4. 建立/編輯風險規則（需 `risk_mgmt` 權限）：
   - 定義條件（例如「Platinum 比率 > 5%」）
   - 設定嚴重等級
   - 啟用/停用規則

---

### 6. Data Management（資料管理）

**用途：** 管理系統中所有組態實體的 CRUD 操作。

**子標籤：**
| 實體 | 說明 |
|------|------|
| Plants | 生產廠區定義（例如 TC） |
| Plant Criteria | 各廠區缺陷門檻（例如 TC 的 Blister > 100um） |
| Tanks | 廠區內的成形槽體 |
| ML Items | 熔融損失項目定義 |
| MSL Items | 機械應力等級項目定義 |
| Attribute Items | 屬性品質項目定義 |

**操作步驟：**
1. 選擇實體類型的子標籤
2. 在可排序/篩選的表格中檢視所有記錄
3. 點擊「新增」建立記錄
4. 點擊編輯圖示修改現有記錄
5. 點擊刪除圖示移除（會有確認對話框）
6. 所有變更立即生效

**需要權限：** `data_mgmt`

---

### 7. Admin Dashboard（管理儀表板）

**用途：** 系統管理，包含 ETL 管理及使用者審核。

**ETL 管理：**
- 檢視 4 個 ETL 作業的狀態（上次執行時間、狀態、筆數）
- 手動觸發任一 ETL 作業
- 檢視失敗作業的錯誤日誌

**使用者管理：**
- 審核/拒絕待核准的 SSO 註冊
- 指派角色（admin/editor/viewer）
- 授予功能權限（offload_override、data_mgmt、risk_mgmt）
- 停用使用者

**需要角色：** `admin`

---

## 認證機制

### 登入方式

1. **Azure AD SSO（建議）**
   - 點擊「以 Corning 帳號登入」
   - 透過 Azure AD 認證
   - 驗證是否為 AD 群組 `PCI-Optimization-Access` 的成員
   - 首次使用者會以「待核准」狀態註冊（需管理員審核）

2. **本地帳號**
   - 帳號/密碼登入
   - 密碼使用 bcrypt 雜湊
   - 限制每分鐘最多 5 次嘗試

### Token 流程

```
登入 → Access Token（JWT，8 小時過期）
    → Refresh Token（HttpOnly cookie，7 天過期）

API 請求 → Authorization header 中帶 Bearer token
Token 過期 → POST /api/v1/auth/refresh → 取得新 access token
```

---

## 權限模型

### 角色

| 角色 | 能力 |
|------|------|
| Admin | 完整存取 + 使用者管理 + ETL 控制 |
| Editor | 卸載選擇、出貨、COA（基本操作） |
| Viewer | 所有儀表板唯讀存取 |

### 功能權限（可疊加）

| 權限鍵值 | 授予能力 |
|----------|---------|
| `offload_override` | 選擇不合格品進行卸載 |
| `data_mgmt` | 新增/修改/刪除組態資料 |
| `risk_mgmt` | 新增/修改風險規則 |

Admin 角色隱含擁有所有權限。

---

## ETL（資料管線）

### 排程

每日 ETL 自動執行（可於 `.env` 設定）：

| 時間 | 作業 | 來源 | 說明 |
|------|------|------|------|
| 06:00 | Batch Sync | MESDW（SQL Server） | Crate 批次、切割日期、數量 |
| 06:15 | Defect Sync | Oracle PPDA | 缺陷檢驗結果 |
| 06:30 | Cube MSL Sync | SSAS Cube | 機械應力等級數據 |
| 06:45 | Shipping Import | 共享資料夾（Excel） | 物流出貨排程 |

### 資料來源

| 來源 | 連線方式 | 資料內容 |
|------|---------|---------|
| Oracle PPDA | `oracle+oracledb://training:training@TC_PPDA` | 缺陷檢驗數據 |
| MESDW | `mssql+pyodbc://TCF11SQL2011/MESDW`（Windows 認證） | 批次/crate 中繼資料 |
| SSAS Cube | `Provider=MSOLAP;Data Source=cgtppd;Catalog=ppd` | MSL 聚合數據 |
| Excel 檔案 | 設定的資料夾路徑 | 出貨排程 |

### 手動觸發

Admin 使用者可從管理儀表板手動觸發任一 ETL 作業，適用場景：
- 來源資料修正後重新匯入
- 測試連線
- 非排程時段的資料更新

---

## API 參考

基本 URL：`http://localhost:8001/api/v1`

### 認證

| 方法 | 端點 | 說明 |
|------|------|------|
| POST | `/auth/login` | 本地帳密登入 |
| POST | `/auth/sso-login` | Azure AD SSO 登入 |
| POST | `/auth/sso-register` | 註冊新 SSO 使用者（待核准） |
| POST | `/auth/refresh` | 更新 access token |
| GET | `/auth/me` | 取得目前使用者資訊 |

### 卸載判定

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/offload/plants` | 列出所有廠區 |
| GET | `/offload/plants/{id}/crates` | 評估廠區的 crate |
| POST | `/offload/selections` | 建立卸載選擇 |
| GET | `/offload/selections` | 列出歷史選擇 |

### 出貨

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/shipping/schedules` | 列出出貨排程 |
| GET | `/shipping/schedules/{id}/assignments` | 取得 crate 分配 |
| POST | `/shipping/schedules/{id}/recalculate` | 重跑 FIFO 分配 |

### COA

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/coa/data` | 取得 COA 數據（缺陷 + MSL） |
| GET | `/coa/export` | 下載 Excel COA 報告 |

### 每日分析

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/analysis/tanks` | 列出槽體 |
| GET | `/analysis/items/{type}` | 列出項目（ml/msl/attribute） |
| GET | `/analysis/ml` | ML 圖表數據 |
| GET | `/analysis/msl` | MSL 圖表數據 |
| GET | `/analysis/attribute` | Attribute 圖表數據 |

### 風險管理

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/risk/crates` | 依等級取得風險 crate |
| GET | `/risk/rules` | 列出風險規則 |
| POST | `/risk/rules` | 建立風險規則 |
| PUT | `/risk/rules/{id}` | 更新風險規則 |
| DELETE | `/risk/rules/{id}` | 刪除風險規則 |

### 資料管理

| 方法 | 端點 | 說明 |
|------|------|------|
| GET/POST | `/data-management/plants` | 列出/建立廠區 |
| PUT/DELETE | `/data-management/plants/{id}` | 更新/刪除廠區 |
| GET/POST | `/data-management/criteria` | 列出/建立判定標準 |
| PUT/DELETE | `/data-management/criteria/{id}` | 更新/刪除判定標準 |
| GET/POST | `/data-management/tanks` | 列出/建立槽體 |
| PUT/DELETE | `/data-management/tanks/{id}` | 更新/刪除槽體 |
| GET/POST | `/data-management/ml-items` | 列出/建立 ML 項目 |
| PUT/DELETE | `/data-management/ml-items/{id}` | 更新/刪除 ML 項目 |
| GET/POST | `/data-management/msl-items` | 列出/建立 MSL 項目 |
| PUT/DELETE | `/data-management/msl-items/{id}` | 更新/刪除 MSL 項目 |
| GET/POST | `/data-management/attribute-items` | 列出/建立 Attribute 項目 |
| PUT/DELETE | `/data-management/attribute-items/{id}` | 更新/刪除 Attribute 項目 |

### 管理

| 方法 | 端點 | 說明 |
|------|------|------|
| GET | `/admin/etl/status` | ETL 作業狀態 |
| POST | `/admin/etl/trigger/{job_name}` | 手動觸發 ETL 作業 |
| GET | `/admin/users` | 列出所有使用者 |
| PUT | `/admin/users/{id}` | 更新使用者角色/狀態/權限 |

---

## 環境變數

### 後端（.env）

```env
# 資料庫
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5433/pci_optimization

# JWT
JWT_SECRET=your-secret-key-here
JWT_EXPIRY_HOURS=8
JWT_REFRESH_EXPIRY_DAYS=7

# Azure AD
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_TENANT_ID=your-tenant-id
AD_REQUIRED_GROUP=PCI-Optimization-Access

# LDAP 服務帳號
LDAP_BIND_DN=corning.com\\svc_pci_app
LDAP_BIND_PASSWORD=service-account-password

# ETL 資料來源
PPDA_CONN=oracle+oracledb://training:training@TC_PPDA
MESDW_CONN=mssql+pyodbc://TCF11SQL2011/MESDW?Trusted_Connection=yes&driver=SQL+Server
CUBE_CONN=Provider=MSOLAP;Data Source=cgtppd;Catalog=ppd;
ADOMD_DLL_PATH=C:\path\to\Microsoft.AnalysisServices.AdomdClient.dll
SHIPPING_FOLDER=\\\\server\\share\\shipping

# ETL 開關
ETL_ENABLED=true
```

### 前端（.env）

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_AZURE_AD_CLIENT_ID=your-client-id
VITE_AZURE_AD_TENANT_ID=your-tenant-id
```

---

## 專案結構

```
backend/
├── app/
│   ├── config.py           # Pydantic 設定（讀取 .env）
│   ├── database.py         # SQLAlchemy 引擎與 session
│   ├── dependencies.py     # FastAPI 依賴注入（認證、DB、權限）
│   ├── main.py             # 應用程式進入點 + lifespan
│   ├── seed.py             # 初始資料匯入
│   ├── models/             # SQLAlchemy ORM 模型
│   │   ├── user.py         # User + UserPermission
│   │   ├── offload.py      # Plant, PlantCriteria, OffloadSelection
│   │   ├── shipping.py     # ShippingSchedule, ShippingAssignment
│   │   ├── analysis.py     # Tank, MlItem, MslItem, AttributeItem, AnalysisData
│   │   ├── risk.py         # RiskRule, RiskCrate
│   │   └── etl.py          # EtlJob（執行紀錄）
│   ├── routers/            # API 端點定義
│   │   ├── auth.py         # 認證（登入、SSO、refresh）
│   │   ├── offload.py      # PCI 卸載操作
│   │   ├── shipping.py     # 出貨 FIFO 邏輯
│   │   ├── coa.py          # COA 數據 + Excel 匯出
│   │   ├── analysis.py     # 每日分析圖表數據
│   │   ├── risk.py         # 風險管理
│   │   ├── data_management.py  # 組態 CRUD
│   │   └── admin.py        # ETL + 使用者管理
│   ├── schemas/            # Pydantic 請求/回應結構
│   ├── services/           # 業務邏輯層
│   │   ├── auth_service.py
│   │   ├── offload_service.py
│   │   └── shipping_service.py
│   ├── etl/                # ETL 作業 + 排程器
│   │   ├── scheduler.py    # APScheduler cron 設定
│   │   ├── connections.py  # Oracle + MSSQL 連線管理
│   │   ├── batch_sync.py   # MESDW → PostgreSQL
│   │   ├── defect_sync.py  # Oracle PPDA → PostgreSQL
│   │   ├── cube_sync.py    # SSAS Cube → PostgreSQL
│   │   └── shipping_import.py  # Excel → PostgreSQL
│   ├── middleware/         # 速率限制
│   └── utils/              # 安全性、Azure AD、LDAP
├── alembic/                # 資料庫遷移
├── requirements.txt
└── .env.example

frontend/
├── src/
│   ├── App.tsx             # 根元件：MSAL + Auth + Router
│   ├── components/         # 共用 UI（佈局、表格、表單）
│   ├── features/           # 功能模組
│   │   ├── auth/           # 登入頁面 + SSO 流程
│   │   ├── offload/        # PCI 卸載標籤頁
│   │   ├── shipping/       # 出貨假設標籤頁
│   │   ├── coa/            # COA 標籤頁
│   │   ├── daily-analysis/ # ML/MSL/Attribute 圖表
│   │   ├── risk/           # 風險管理標籤頁
│   │   ├── data-mgmt/      # 資料管理標籤頁
│   │   └── admin/          # 管理儀表板
│   ├── lib/                # API 客戶端、認證 context、工具函式
│   └── hooks/              # 自訂 React hooks
├── vite.config.ts
├── tailwind.config.ts
└── package.json
```

---

## 連接埠

| 服務 | Port |
|------|------|
| 前端 | 8080 |
| 後端 | 8001 |
| PostgreSQL | 5433 |

---

## 部署（Windows Server）

### 正式環境設定

1. **PostgreSQL**：安裝並設定於 port 5433
2. **後端**：使用正式 ASGI 伺服器執行
   ```bash
   pip install gunicorn uvicorn[standard]
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
   ```
3. **前端**：建置並透過 nginx 或 IIS 提供服務
   ```bash
   cd frontend
   npm run build
   # 將 dist/ 資料夾部署至 Web 伺服器
   ```
4. **ETL**：確保伺服器可存取 Oracle、MSSQL、SSAS
5. **Windows 服務**：使用 NSSM 或工作排程器將後端設為服務

### 網路需求

| 來源 | 目的地 | Port | 協定 |
|------|--------|------|------|
| 後端 | PostgreSQL | 5433 | TCP |
| 後端 | Oracle PPDA | 1521 | TCP |
| 後端 | MESDW SQL Server | 1433 | TCP |
| 後端 | SSAS Cube (cgtppd) | 2383 | TCP |
| 後端 | AD (ap.corning.com) | 636 | LDAPS |
| 前端 | 後端 | 8001 | HTTP |
| 使用者 | 前端 | 8080 | HTTP |

---

## 疑難排解

### 常見問題

**「LDAP bind failed」**
- 確認 `.env` 中的服務帳號憑證正確
- 檢查是否可連線至 ap.corning.com:636
- 確認使用者位於 DC=ap,DC=corning,DC=com 下的正確 OU

**「ETL job failed」**
- 至管理儀表板查看錯誤詳情
- 確認來源資料庫連線
- SSAS Cube：確認 ADOMD DLL 路徑正確
- Shipping Import：確認 Excel 檔案格式符合預期結構

**「Token expired」**
- 前端會自動更新 token
- 若 refresh 失敗，使用者會被導回登入頁
- 確認 JWT_SECRET 在不同 session 間沒有變更

**「Permission denied」**
- 至管理儀表板確認使用者角色及功能權限
- Admin 角色隱含擁有所有權限
- 功能權限（offload_override、data_mgmt、risk_mgmt）需明確授予

**Python 3.13+ MD4 錯誤**
- 系統包含純 Python MD4 fallback 實作，用於 NTLM 認證
- 當 OpenSSL 3.0+ 移除 MD4 支援時會自動啟用
- 無需額外操作 — monkey-patch 會透明處理

---

## 開發

### 執行測試

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

### 資料庫遷移

```bash
cd backend

# 建立新遷移
alembic revision --autogenerate -m "description"

# 套用遷移
alembic upgrade head

# 回滾一步
alembic downgrade -1
```

### API 文件

FastAPI 自動產生互動式文件：
- Swagger UI：http://localhost:8001/docs
- ReDoc：http://localhost:8001/redoc

---

## Legacy Config 參考

根目錄的 `config.py` 為 Web 系統建置前的舊版設定檔，記錄了領域知識：

- **DEFECT_DICT**：缺陷類型代碼對應名稱（0-8）
- **RECEIVER_SPECS**：客戶特定缺陷門檻（例如 TC 廠區標準）
- **DEFECT_SHORT_NAMES**：Cube 缺陷 ID 縮寫（例如「A-side adhered glass full sheet」→「A-ADG」）
- **MSL_COLUMNS**：報告中 MSL 欄位的標準順序
- **COMPOSITE_COLUMNS**：加總多個缺陷類型的計算欄位
- **CUBE_RENAME / CUBE_DEFECT_COL / CUBE_VALUE_COL**：SSAS Cube MDX 欄位對應

此設定已遷移至 Web 系統的資料庫（透過資料管理標籤頁維護），但檔案保留作為領域參考。
