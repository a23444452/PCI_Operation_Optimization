# Backend CLAUDE.md — PCI Hermes Platform

## Azure AD Access Token 驗證

| 欄位 | 值 |
|------|---|
| audience | `api://{AZURE_AD_CLIENT_ID}` |
| issuer | `https://sts.windows.net/{AZURE_AD_TENANT_ID}/` |
| username claim | `upn` (非 `preferred_username`) |
| 演算法 | RS256, JWKS from Microsoft |

Azure Portal 前置設定:
1. Expose an API → Application ID URI = `api://{client_id}`
2. Add scope: `RBAC`（Admins and users consent）
3. API Permissions → Grant admin consent

- ❌ 不要用 ID Token 的 audience/issuer（格式不同）
- ❌ 不要猜 scope 名稱 — 必須先在 Azure Portal 建立

## SSO 註冊審批流程

```
新使用者 SSO → AD Group 驗證 → 建立 pending 帳號
  → email 通知 admin（含使用者資訊）
  → email 通知使用者（等待審核）
  → admin approve/reject
  → email 通知使用者結果
```

## Tech Stack

- FastAPI + SQLAlchemy + SQLite(dev) / SQL Server(prod)
- PyJWT + httpx（Azure AD token 驗證）
- ldap3 + NTLM（AD Group 查詢）
- smtplib（Corning 內部 SMTP: `smtphub.corning.com:25`，無需認證）

## 環境變數

| 變數 | 說明 |
|------|------|
| `AZURE_AD_CLIENT_ID` | Azure AD App Registration client ID |
| `AZURE_AD_TENANT_ID` | Azure AD tenant ID |
| `AD_REQUIRED_GROUP` | 必要的 AD Group（入口閘門） |
| `LDAP_BIND_DN` | LDAP service account（`ap\account` 單反斜線） |
| `LDAP_BIND_PASSWORD` | LDAP 密碼 |
| `ADMIN_NOTIFICATION_EMAILS` | 管理員 email（逗號分隔） |
