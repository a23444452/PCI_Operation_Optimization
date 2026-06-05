import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, AlertCircle, UserCheck, UserX } from "lucide-react";
import api from "@/lib/api";

interface User {
  id: number;
  username: string;
  display_name: string;
  email: string;
  role: string;
  status: string;
  permissions: string[];
}

const ROLES = ["admin", "editor", "viewer"];
const STATUSES = ["active", "inactive", "pending"];
const PERMISSION_OPTIONS = ["offload_override", "data_mgmt", "risk_mgmt"];

export function UsersPage() {
  const queryClient = useQueryClient();
  const [approveTarget, setApproveTarget] = useState<User | null>(null);
  const [approveRole, setApproveRole] = useState("viewer");
  const [approvePermissions, setApprovePermissions] = useState<string[]>([]);
  const [rejectTarget, setRejectTarget] = useState<User | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  const {
    data: users,
    isLoading,
    error,
  } = useQuery<User[]>({
    queryKey: ["admin-users"],
    queryFn: async () => {
      const res = await api.get("/users");
      return res.data.data;
    },
  });

  const roleMutation = useMutation({
    mutationFn: async ({ id, role }: { id: number; role: string }) => {
      const res = await api.patch(`/users/${id}/role`, { role });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: number; status: string }) => {
      const res = await api.patch(`/users/${id}/status`, { status });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const permissionMutation = useMutation({
    mutationFn: async ({ id, permissions }: { id: number; permissions: string[] }) => {
      const res = await api.put(`/users/${id}/permissions`, { permissions });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: async ({ id, role, permissions }: { id: number; role: string; permissions: string[] }) => {
      const res = await api.put(`/users/${id}/approve`, { role, permissions });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setApproveTarget(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: number; reason: string | null }) => {
      const res = await api.put(`/users/${id}/reject`, { reason });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setRejectTarget(null);
      setRejectReason("");
    },
  });

  function handlePermissionToggle(user: User, permission: string) {
    const current = user.permissions ?? [];
    const updated = current.includes(permission)
      ? current.filter((p) => p !== permission)
      : [...current, permission];
    permissionMutation.mutate({ id: user.id, permissions: updated });
  }

  function openApproveDialog(user: User) {
    setApproveTarget(user);
    setApproveRole("viewer");
    setApprovePermissions([]);
  }

  function openRejectDialog(user: User) {
    setRejectTarget(user);
    setRejectReason("");
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Loading users...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
        <AlertCircle className="h-5 w-5" />
        <span>Failed to load users. Please try again.</span>
      </div>
    );
  }

  const pendingUsers = users?.filter((u) => u.status === "pending") ?? [];
  const activeUsers = users?.filter((u) => u.status !== "pending" && u.status !== "rejected") ?? [];

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900">User Management</h3>

      {/* Pending Approval Section */}
      {pendingUsers.length > 0 && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-yellow-800">
            <AlertCircle className="h-4 w-4" />
            Pending Approval ({pendingUsers.length})
          </h4>
          <div className="space-y-2">
            {pendingUsers.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between rounded-md border border-yellow-100 bg-white px-4 py-3"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{user.display_name}</p>
                  <p className="text-xs text-gray-500">
                    {user.username} &middot; {user.email}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => openApproveDialog(user)}
                    className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700"
                  >
                    <UserCheck className="h-3.5 w-3.5" />
                    Approve
                  </button>
                  <button
                    onClick={() => openRejectDialog(user)}
                    className="inline-flex items-center gap-1 rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-red-700"
                  >
                    <UserX className="h-3.5 w-3.5" />
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active Users Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Username
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Display Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Email
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Role
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Permissions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {activeUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                  {user.username}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                  {user.display_name}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                  {user.email}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  <select
                    value={user.role}
                    onChange={(e) => roleMutation.mutate({ id: user.id, role: e.target.value })}
                    className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  <select
                    value={user.status}
                    onChange={(e) => statusMutation.mutate({ id: user.id, status: e.target.value })}
                    className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-4 py-3 text-sm">
                  <div className="flex flex-wrap gap-2">
                    {PERMISSION_OPTIONS.map((perm) => (
                      <label key={perm} className="inline-flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={user.permissions?.includes(perm) ?? false}
                          onChange={() => handlePermissionToggle(user, perm)}
                          className="h-3.5 w-3.5 rounded border-gray-300"
                        />
                        <span className="text-gray-700">{perm}</span>
                      </label>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {activeUsers.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500">
                  No users found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Approve Dialog */}
      {approveTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h4 className="text-lg font-semibold text-gray-900">Approve User</h4>
            <p className="mt-1 text-sm text-gray-500">
              Approve <strong>{approveTarget.display_name}</strong> ({approveTarget.username})
            </p>

            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Role</label>
                <select
                  value={approveRole}
                  onChange={(e) => setApproveRole(e.target.value)}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Permissions</label>
                <div className="mt-2 space-y-2">
                  {PERMISSION_OPTIONS.map((perm) => (
                    <label key={perm} className="inline-flex items-center gap-2 mr-4 text-sm">
                      <input
                        type="checkbox"
                        checked={approvePermissions.includes(perm)}
                        onChange={() => {
                          setApprovePermissions((prev) =>
                            prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm]
                          );
                        }}
                        className="h-4 w-4 rounded border-gray-300"
                      />
                      <span className="text-gray-700">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setApproveTarget(null)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  approveMutation.mutate({
                    id: approveTarget.id,
                    role: approveRole,
                    permissions: approvePermissions,
                  })
                }
                disabled={approveMutation.isPending}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                {approveMutation.isPending ? "Approving..." : "Approve"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Dialog */}
      {rejectTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h4 className="text-lg font-semibold text-gray-900">Reject User</h4>
            <p className="mt-1 text-sm text-gray-500">
              Reject <strong>{rejectTarget.display_name}</strong> ({rejectTarget.username})
            </p>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">
                Reason (optional)
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                placeholder="Provide a reason for rejection..."
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setRejectTarget(null)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  rejectMutation.mutate({
                    id: rejectTarget.id,
                    reason: rejectReason || null,
                  })
                }
                disabled={rejectMutation.isPending}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                {rejectMutation.isPending ? "Rejecting..." : "Reject"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
