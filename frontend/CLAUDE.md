# Frontend CLAUDE.md — PCI Hermes Platform

## MSAL.js SSO 模式

使用 `loginRedirect` 模式（非 `loginPopup`），參考 Dt_Quality_Roadmap：

| 元件 | 職責 |
|------|------|
| `msal-config.ts` | export `msalInstance`, `loginRequest`, `tokenRequest` |
| `AuthProvider.tsx` | 包裝 `MsalProvider` + `AuthProviderInner`，`ssoLogin()` 無參數 |
| `LoginPage.tsx` | dual-path: `useEffect`(redirect) + click handler(silent) |

SSO 流程：
1. 無快取 → `loginRedirect` + `sessionStorage('sso_redirect_pending')`
2. 有快取 → `acquireTokenSilent` → fallback `acquireTokenRedirect`
3. 取得 access_token → POST `/auth/sso-login` → 處理三種狀態

| 狀態 | 意義 | 前端行為 |
|------|------|---------|
| `authenticated` | 已核准使用者 | navigate to `/offload` |
| `need_registration` | 新使用者 | 呼叫 `/sso-register` → 顯示等待訊息 |
| `pending_approval` | 等待審核 | 顯示等待訊息 |

- ❌ 不要用 `loginPopup` — SPA 會在 popup 中渲染完整應用程式
- ❌ 不要手動在 main.tsx 呼叫 `msalInstance.initialize()` — `MsalProvider` 自動處理
- ❌ 不要在 `ssoLogin()` 外部取得 access token — 由 AuthProvider 內部管理

## Tech Stack

- React 18 + TypeScript + Vite
- TanStack Query (React Query)
- TailwindCSS + custom dark theme
- `@azure/msal-browser` ^5.x + `@azure/msal-react` ^2.x
- axios（`/lib/api.ts` 封裝，自動加 Bearer token）
