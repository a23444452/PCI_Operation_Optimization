import { createContext, useCallback, useEffect, useState, type ReactNode } from "react";
import api from "@/lib/api";

export interface UserInfo {
  id: number;
  username: string;
  display_name: string;
  role: string;
  permissions: string[];
}

export interface AuthContextType {
  user: UserInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  ssoLogin: (accessToken: string) => Promise<SSOLoginResult>;
  logout: () => void;
}

export type SSOLoginResult =
  | { status: "authenticated"; user: UserInfo }
  | { status: "need_registration"; username: string; email: string; display_name: string }
  | { status: "pending_approval"; username: string };

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      api.get("/auth/me")
        .then((res) => setUser(res.data.data))
        .catch(() => {
          localStorage.removeItem("access_token");
          setUser(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post("/auth/login", { username, password });
    const { access_token, user: userInfo } = res.data.data;
    localStorage.setItem("access_token", access_token);
    setUser(userInfo);
  }, []);

  const ssoLogin = useCallback(async (accessToken: string): Promise<SSOLoginResult> => {
    const res = await api.post("/auth/sso-login", { access_token: accessToken });
    const data = res.data.data;

    if (data.status === "authenticated") {
      localStorage.setItem("access_token", data.access_token);
      setUser(data.user);
      return { status: "authenticated", user: data.user };
    }
    return data as SSOLoginResult;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, ssoLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
