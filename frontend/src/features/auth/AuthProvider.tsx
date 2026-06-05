import { createContext, useCallback, useEffect, useState, type ReactNode } from "react";
import { MsalProvider, useMsal } from "@azure/msal-react";
import { InteractionStatus } from "@azure/msal-browser";
import api from "@/lib/api";
import { msalInstance, loginRequest, tokenRequest } from "@/lib/msal-config";

export interface UserInfo {
  id: number;
  username: string;
  display_name: string;
  role: string;
  permissions: string[];
}

export type SSOLoginResult =
  | { status: "authenticated"; user: UserInfo }
  | { status: "need_registration"; username: string; email: string; display_name: string; access_token: string }
  | { status: "pending_approval"; username: string };

export interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  ssoLogin: () => Promise<SSOLoginResult>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

function AuthProviderInner({ children }: { children: ReactNode }) {
  const { instance, inProgress } = useMsal();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
      }
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (inProgress !== InteractionStatus.None) return;
    instance.handleRedirectPromise().catch(() => {});
  }, [instance, inProgress]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post("/auth/login", { username, password });
    const { access_token, user: userInfo } = res.data.data;
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("user", JSON.stringify(userInfo));
    setUser(userInfo);
  }, []);

  const ssoLogin = useCallback(async (): Promise<SSOLoginResult> => {
    const accounts = instance.getAllAccounts();

    if (accounts.length === 0) {
      sessionStorage.setItem("sso_redirect_pending", "1");
      await instance.loginRedirect(loginRequest);
      throw new Error("Redirecting to Azure AD");
    }

    let accessToken: string;
    try {
      const tokenResponse = await instance.acquireTokenSilent({
        ...tokenRequest,
        account: accounts[0],
      });
      accessToken = tokenResponse.accessToken;
    } catch {
      await instance.acquireTokenRedirect(tokenRequest);
      throw new Error("Redirecting to acquire token");
    }

    const res = await api.post("/auth/sso-login", { access_token: accessToken });
    const data = res.data.data;

    if (data.status === "authenticated") {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      setUser(data.user);
      return { status: "authenticated", user: data.user };
    }

    if (data.status === "need_registration") {
      return { ...data, access_token: accessToken } as SSOLoginResult;
    }

    return data as SSOLoginResult;
  }, [instance]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, ssoLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthProviderInner>{children}</AuthProviderInner>
    </MsalProvider>
  );
}
