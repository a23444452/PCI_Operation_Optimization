import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMsal } from "@azure/msal-react";
import { InteractionStatus } from "@azure/msal-browser";
import { Mail } from "lucide-react";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";

export function LoginPage() {
  const navigate = useNavigate();
  const { login, ssoLogin } = useAuth();
  const { inProgress } = useMsal();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [adminEmails, setAdminEmails] = useState<string[]>([]);

  useEffect(() => {
    api.get("/auth/system-config")
      .then((res) => {
        const emails = res.data?.data?.admin_emails ?? [];
        setAdminEmails(emails);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (inProgress !== InteractionStatus.None) return;
    if (!sessionStorage.getItem("sso_redirect_pending")) return;
    sessionStorage.removeItem("sso_redirect_pending");

    setIsLoading(true);
    ssoLogin()
      .then((result) => {
        if (result.status === "authenticated") {
          navigate("/offload", { replace: true });
        } else if (result.status === "pending_approval") {
          setInfo("Your account is awaiting administrator approval.");
        } else if (result.status === "need_registration") {
          api.post("/auth/sso-register", {
            access_token: result.access_token,
          }).then(() => {
            setInfo("Account registered successfully. Awaiting administrator approval.");
          }).catch(() => {
            setInfo("Registration submitted. Awaiting administrator approval.");
          });
        }
      })
      .catch((err) => {
        if (err instanceof Error && err.message === "Redirecting to Azure AD") return;
        const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
        if (axiosErr.response?.status === 403) {
          setError("Access denied. You are not a member of the required AD group.");
        } else {
          setError("Sign-in failed. Please try again.");
        }
      })
      .finally(() => setIsLoading(false));
  }, [inProgress, ssoLogin, navigate]);

  const handleSSOClick = async () => {
    setError("");
    setInfo("");
    setIsLoading(true);
    try {
      const result = await ssoLogin();
      if (result.status === "authenticated") {
        navigate("/offload", { replace: true });
      } else if (result.status === "pending_approval") {
        setInfo("Your account is awaiting administrator approval.");
      } else if (result.status === "need_registration") {
        await api.post("/auth/sso-register", {
          access_token: result.access_token,
        });
        setInfo("Account registered successfully. Awaiting administrator approval.");
      }
    } catch (err) {
      if (err instanceof Error && err.message === "Redirecting to Azure AD") return;
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      if (axiosErr.response?.status === 403) {
        setError("Access denied. You are not a member of the required AD group.");
      } else {
        setError("Sign-in failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLocalLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setIsLoading(true);
    try {
      await login(username, password);
      navigate("/offload");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-[100dvh] items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/20 via-transparent to-transparent" />
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjAuNSIgZmlsbD0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIvPjwvc3ZnPg==')] opacity-60" />

      <div className="relative z-10 w-full max-w-md px-4">
        <div className="mb-3 flex flex-col items-center">
          <img
            src="/PCI_Logo_V1.png"
            alt="PCI Logo"
            className="mb-1 h-48 w-48 object-contain"
          />
          <h1 className="text-xl font-semibold tracking-wide text-white">
            PCI Hermes Platform
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Process Continuous Improvement
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur-sm">
          {info && (
            <div className="mb-4 rounded-md bg-cyan-900/30 px-3 py-2 text-sm text-cyan-300">
              {info}
            </div>
          )}

          <button
            onClick={handleSSOClick}
            disabled={isLoading}
            className="mb-6 w-full rounded-lg bg-accent px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-50"
          >
            {isLoading ? "Signing in..." : "Login with Corning SSO"}
          </button>

          <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-transparent px-2 text-slate-400">or</span>
            </div>
          </div>

          <form onSubmit={handleLocalLogin} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-600 disabled:opacity-50"
            >
              Login
            </button>
          </form>

          {error && (
            <p className="mt-4 text-center text-sm text-red-400">{error}</p>
          )}
        </div>

        {adminEmails.length > 0 && (
          <div className="mt-4 text-center">
            <p className="flex items-center justify-center gap-1 text-xs text-slate-500">
              <Mail className="h-3 w-3" />
              Admin Contact
            </p>
            {adminEmails.map((email) => (
              <a
                key={email}
                href={`mailto:${email}`}
                className="block text-xs text-slate-400 hover:text-white transition-colors"
              >
                {email}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
