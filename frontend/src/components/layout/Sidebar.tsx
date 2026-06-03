import { NavLink, useNavigate } from "react-router-dom";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/features/auth/useAuth";

const navItems = [
  { path: "/offload", label: "PCI Offload", icon: Package },
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

export function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center px-6">
        <h1 className="text-lg font-bold text-gray-900">PCI Optimization</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
        <div className="my-4 border-t border-gray-200" />
        {adminItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-gray-200 p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
