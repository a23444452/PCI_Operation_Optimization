import { useState, useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import {
  Package,
  Truck,
  FileCheck,
  BarChart3,
  LineChart,
  Layers,
  ShieldAlert,
  Database,
  Users,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Mail,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/useAuth";
import api from "@/lib/api";

const navItems = [
  { path: "/offload", label: "PCI Offload Selection", icon: Package },
  { path: "/shipping", label: "Shipping Assumption", icon: Truck },
  { path: "/coa", label: "COA", icon: FileCheck },
  { path: "/analysis/ml", label: "Daily Analysis — ML", icon: BarChart3 },
  { path: "/analysis/msl", label: "Daily Analysis — MSL", icon: LineChart },
  { path: "/analysis/attribute", label: "Daily Analysis — Attribute", icon: Layers },
  { path: "/risk", label: "Risk Management", icon: ShieldAlert },
  { path: "/data-management", label: "Data Management", icon: Database },
];

const adminItems = [
  { path: "/admin/users", label: "User Management", icon: Users },
];

function NavItem({
  item,
  collapsed,
}: {
  item: { path: string; label: string; icon: React.ElementType };
  collapsed: boolean;
}) {
  const location = useLocation();
  const Icon = item.icon;
  const isActive =
    location.pathname === item.path ||
    location.pathname.startsWith(item.path + "/");

  return (
    <NavLink
      to={item.path}
      title={collapsed ? item.label : undefined}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        collapsed ? "justify-center px-2" : "",
        isActive
          ? "bg-white/10 text-cyan-400"
          : "text-slate-300 hover:bg-slate-800 hover:text-white"
      )}
    >
      <Icon size={20} className="shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </NavLink>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [adminEmails, setAdminEmails] = useState<string[]>([]);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/auth/system-config")
      .then((res) => {
        const emails = res.data?.data?.admin_emails ?? [];
        setAdminEmails(emails);
      })
      .catch(() => {});
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside
      className={cn(
        "flex flex-col bg-sidebar text-white transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo area */}
      <div className="flex h-56 items-center justify-center border-b border-white/10 px-2">
        <img
          src="/PCI_Logo_V1.png"
          alt="PCI Hermes Platform"
          className={cn(
            "object-contain",
            collapsed ? "h-10 w-10" : "h-56"
          )}
        />
      </div>

      {/* Main nav */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-4">
        {navItems.map((item) => (
          <NavItem key={item.path} item={item} collapsed={collapsed} />
        ))}

        <div className="my-3 border-t border-white/10" />

        {!collapsed && (
          <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Admin
          </p>
        )}
        {adminItems.map((item) => (
          <NavItem key={item.path} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Admin Contact */}
      {adminEmails.length > 0 && (
        <div className="border-t border-white/10 px-2 py-3">
          {collapsed ? (
            <div className="flex justify-center" title={adminEmails.join(", ")}>
              <Mail size={16} className="text-slate-500" />
            </div>
          ) : (
            <div className="space-y-1">
              <p className="flex items-center gap-1.5 px-3 text-xs font-medium text-slate-500">
                <Mail size={12} />
                Admin Contact
              </p>
              {adminEmails.map((email) => (
                <a
                  key={email}
                  href={`mailto:${email}`}
                  className="block truncate px-3 text-xs text-slate-400 hover:text-cyan-400 transition-colors"
                >
                  {email}
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Logout */}
      <div className="border-t border-white/10 p-2">
        <button
          onClick={handleLogout}
          title={collapsed ? "Logout" : undefined}
          className={cn(
            "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition-colors",
            collapsed ? "justify-center px-2" : ""
          )}
        >
          <LogOut size={18} className="shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <div className="border-t border-white/10 p-2">
        <button
          onClick={() => setCollapsed((prev) => !prev)}
          className="flex w-full items-center justify-center rounded-md px-2 py-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
    </aside>
  );
}
