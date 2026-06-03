import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Check, X, Loader2, AlertCircle } from "lucide-react";
import api from "@/lib/api";

interface ColumnDef {
  key: string;
  label: string;
  type?: "text" | "number" | "boolean";
}

interface CrudTableProps {
  title: string;
  endpoint: string;
  columns: ColumnDef[];
  createFields: ColumnDef[];
}

export function CrudTable({ title, endpoint, columns, createFields }: CrudTableProps) {
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Record<string, unknown>>({});
  const [editData, setEditData] = useState<Record<string, unknown>>({});

  const {
    data: items,
    isLoading,
    error,
  } = useQuery<Record<string, unknown>[]>({
    queryKey: ["data-mgmt", endpoint],
    queryFn: async () => {
      const res = await api.get(`/data-mgmt${endpoint}`);
      return res.data.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const res = await api.post(`/data-mgmt${endpoint}`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-mgmt", endpoint] });
      setShowCreateForm(false);
      setFormData({});
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Record<string, unknown> }) => {
      const res = await api.put(`/data-mgmt${endpoint}/${id}`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-mgmt", endpoint] });
      setEditingId(null);
      setEditData({});
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await api.delete(`/data-mgmt${endpoint}/${id}`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["data-mgmt", endpoint] });
    },
  });

  function handleCreate() {
    createMutation.mutate(formData);
  }

  function handleStartEdit(item: Record<string, unknown>) {
    setEditingId(item.id as number);
    const data: Record<string, unknown> = {};
    for (const col of columns) {
      data[col.key] = item[col.key];
    }
    setEditData(data);
  }

  function handleSaveEdit() {
    if (editingId === null) return;
    updateMutation.mutate({ id: editingId, data: editData });
  }

  function handleDelete(id: number) {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    deleteMutation.mutate(id);
  }

  function renderFieldInput(
    field: ColumnDef,
    value: unknown,
    onChange: (key: string, val: unknown) => void
  ) {
    if (field.type === "boolean") {
      return (
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(field.key, e.target.checked)}
          className="h-4 w-4 rounded border-gray-300"
        />
      );
    }
    if (field.type === "number") {
      return (
        <input
          type="number"
          value={value as number ?? ""}
          onChange={(e) => onChange(field.key, e.target.value ? Number(e.target.value) : "")}
          className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
      );
    }
    return (
      <input
        type="text"
        value={(value as string) ?? ""}
        onChange={(e) => onChange(field.key, e.target.value)}
        className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <button
          onClick={() => {
            setShowCreateForm(true);
            const defaults: Record<string, unknown> = {};
            for (const f of createFields) {
              defaults[f.key] = f.type === "boolean" ? false : f.type === "number" ? 0 : "";
            }
            setFormData(defaults);
          }}
          className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <Plus className="h-4 w-4" />
          Add
        </button>
      </div>

      {showCreateForm && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h4 className="mb-3 text-sm font-medium text-gray-700">New {title}</h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {createFields.map((field) => (
              <div key={field.key}>
                <label className="mb-1 block text-xs font-medium text-gray-600">
                  {field.label}
                </label>
                {renderFieldInput(field, formData[field.key], (key, val) =>
                  setFormData({ ...formData, [key]: val })
                )}
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={handleCreate}
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {createMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Check className="h-3.5 w-3.5" />
              )}
              Save
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <X className="h-3.5 w-3.5" />
              Cancel
            </button>
          </div>
          {createMutation.isError && (
            <p className="mt-2 text-sm text-red-600">Failed to create. Please try again.</p>
          )}
        </div>
      )}

      {isLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading...</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load data. Please try again.</span>
        </div>
      )}

      {items && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  ID
                </th>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  >
                    {col.label}
                  </th>
                ))}
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {items.map((item) => {
                const isEditing = editingId === (item.id as number);
                return (
                  <tr key={item.id as number} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                      {item.id as number}
                    </td>
                    {columns.map((col) => (
                      <td key={col.key} className="whitespace-nowrap px-4 py-3 text-sm">
                        {isEditing ? (
                          renderFieldInput(col, editData[col.key], (key, val) =>
                            setEditData({ ...editData, [key]: val })
                          )
                        ) : col.type === "boolean" ? (
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                              item[col.key] ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {item[col.key] ? "Yes" : "No"}
                          </span>
                        ) : (
                          <span className="text-gray-900">{String(item[col.key] ?? "")}</span>
                        )}
                      </td>
                    ))}
                    <td className="whitespace-nowrap px-4 py-3 text-right text-sm">
                      {isEditing ? (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={handleSaveEdit}
                            disabled={updateMutation.isPending}
                            className="rounded p-1 text-green-600 hover:bg-green-50"
                            title="Save"
                          >
                            <Check className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="rounded p-1 text-gray-500 hover:bg-gray-100"
                            title="Cancel"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => handleStartEdit(item)}
                            className="rounded p-1 text-blue-600 hover:bg-blue-50"
                            title="Edit"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(item.id as number)}
                            disabled={deleteMutation.isPending}
                            className="rounded p-1 text-red-600 hover:bg-red-50"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
              {items.length === 0 && (
                <tr>
                  <td
                    colSpan={columns.length + 2}
                    className="px-4 py-8 text-center text-sm text-gray-500"
                  >
                    No items found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
