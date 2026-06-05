import { Users, UserCheck, UserX, Shield } from "lucide-react";

export function UsersPage() {
  const kpiCards = [
    { title: "Total Users", value: "—", icon: Users, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Active", value: "—", icon: UserCheck, accent: "text-green-600", iconBg: "bg-green-50" },
    { title: "Pending Approval", value: "—", icon: UserX, accent: "text-yellow-600", iconBg: "bg-yellow-50" },
    { title: "Admins", value: "—", icon: Shield, accent: "text-purple-600", iconBg: "bg-purple-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage user accounts, roles, and permissions
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-500">{card.title}</p>
                <div className={`rounded-lg p-2 ${card.iconBg}`}>
                  <Icon className={`h-4 w-4 ${card.accent}`} />
                </div>
              </div>
              <p className={`mt-3 text-3xl font-bold ${card.accent}`}>{card.value}</p>
            </div>
          );
        })}
      </div>

      {/* Users Table Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Users</h2>
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Search users..."
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
            <select className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500">
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Username</th>
                  <th className="px-4 py-3">Display Name</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last Login</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    No users found.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
