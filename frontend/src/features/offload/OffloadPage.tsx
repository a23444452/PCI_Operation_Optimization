import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type RowSelectionState,
} from "@tanstack/react-table";
import {
  CheckCircle2,
  XCircle,
  Lock,
  Loader2,
  AlertCircle,
  ArrowUpDown,
} from "lucide-react";
import api from "@/lib/api";
import { useAuth } from "@/features/auth/useAuth";
import { usePlants } from "./usePlants";

interface DefectRatios {
  [type: string]: number;
}

interface Crate {
  crate_id: string;
  batch_id: string;
  in_qty: number;
  cut_lot_end_date: string;
  defect_ratios: DefectRatios;
  is_compliant: boolean;
  failed_criteria: string[];
}

const columnHelper = createColumnHelper<Crate>();

const BADGE_COLORS = [
  "bg-blue-100 text-blue-800",
  "bg-amber-100 text-amber-800",
  "bg-purple-100 text-purple-800",
  "bg-red-100 text-red-800",
  "bg-green-100 text-green-800",
];

export function OffloadPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [plantId, setPlantId] = useState<number | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});

  const hasOverridePermission = user?.permissions.includes("offload_override") ?? false;

  const { data: plants, isLoading: plantsLoading } = usePlants();

  const {
    data: crates,
    isLoading: cratesLoading,
    error: cratesError,
  } = useQuery<Crate[]>({
    queryKey: ["offload-crates", plantId],
    queryFn: async () => {
      const res = await api.get("/offload/crates", { params: { plant_id: plantId } });
      return res.data.data;
    },
    enabled: plantId !== null,
  });

  const selectMutation = useMutation({
    mutationFn: async (crateIds: string[]) => {
      const res = await api.post("/offload/select", {
        plant_id: plantId,
        crate_ids: crateIds,
      });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["offload-crates", plantId] });
      setRowSelection({});
    },
  });

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "select",
        header: ({ table }) => (
          <input
            type="checkbox"
            checked={table.getIsAllPageRowsSelected()}
            onChange={table.getToggleAllPageRowsSelectedHandler()}
            className="h-4 w-4 rounded border-gray-300"
          />
        ),
        cell: ({ row }) => {
          const canSelect = row.original.is_compliant || hasOverridePermission;
          return canSelect ? (
            <input
              type="checkbox"
              checked={row.getIsSelected()}
              onChange={row.getToggleSelectedHandler()}
              className="h-4 w-4 rounded border-gray-300"
            />
          ) : (
            <Lock className="h-4 w-4 text-gray-400" />
          );
        },
      }),
      columnHelper.accessor("crate_id", {
        header: "Crate ID",
        cell: (info) => <span className="font-mono text-sm">{info.getValue()}</span>,
      }),
      columnHelper.accessor("batch_id", {
        header: "Batch ID",
        cell: (info) => <span className="font-mono text-sm">{info.getValue()}</span>,
      }),
      columnHelper.accessor("in_qty", {
        header: "In Qty",
        cell: (info) => info.getValue().toLocaleString(),
      }),
      columnHelper.accessor("cut_lot_end_date", {
        header: "Cut Lot End Date",
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor("is_compliant", {
        header: "Compliance",
        cell: (info) =>
          info.getValue() ? (
            <CheckCircle2 className="h-5 w-5 text-green-600" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          ),
      }),
      columnHelper.accessor("defect_ratios", {
        header: "Defect Ratios",
        cell: (info) => {
          const ratios = info.getValue();
          const entries = Object.entries(ratios)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 3);
          return (
            <div className="flex flex-wrap gap-1">
              {entries.map(([type, ratio], idx) => (
                <span
                  key={type}
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${BADGE_COLORS[idx % BADGE_COLORS.length]}`}
                >
                  {type}: {(ratio * 100).toFixed(1)}%
                </span>
              ))}
            </div>
          );
        },
        enableSorting: false,
      }),
    ],
    [hasOverridePermission]
  );

  const table = useReactTable({
    data: crates ?? [],
    columns,
    state: { sorting, rowSelection },
    onSortingChange: setSorting,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: (row) => row.original.is_compliant || hasOverridePermission,
    getRowId: (row) => row.crate_id,
  });

  const selectedCrateIds = Object.keys(rowSelection).filter((id) => rowSelection[id]);

  function handleConfirmSelection() {
    if (selectedCrateIds.length === 0) return;
    selectMutation.mutate(selectedCrateIds);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">PCI Offload</h2>
      </div>

      <div className="flex items-center gap-4">
        <label htmlFor="plant-select" className="text-sm font-medium text-gray-700">
          Plant:
        </label>
        <select
          id="plant-select"
          value={plantId ?? ""}
          onChange={(e) => {
            const val = e.target.value;
            setPlantId(val ? Number(val) : null);
            setRowSelection({});
          }}
          className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          disabled={plantsLoading}
        >
          <option value="">Select a plant...</option>
          {plants?.map((plant) => (
            <option key={plant.id} value={plant.id}>
              {plant.name} ({plant.code})
            </option>
          ))}
        </select>
      </div>

      {plantId === null && (
        <p className="text-sm text-gray-500">Select a plant to view available crates.</p>
      )}

      {cratesLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading crates...</span>
        </div>
      )}

      {cratesError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load crates. Please try again.</span>
        </div>
      )}

      {crates && (
        <>
          <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                      >
                        {header.isPlaceholder ? null : (
                          <div
                            className={
                              header.column.getCanSort()
                                ? "flex cursor-pointer select-none items-center gap-1"
                                : ""
                            }
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            {flexRender(header.column.columnDef.header, header.getContext())}
                            {header.column.getCanSort() && (
                              <ArrowUpDown className="h-3 w-3 text-gray-400" />
                            )}
                          </div>
                        )}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className={
                      row.original.is_compliant
                        ? "hover:bg-gray-50"
                        : "bg-red-50/30 hover:bg-red-50/50"
                    }
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="whitespace-nowrap px-4 py-3 text-sm text-gray-900">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
                {table.getRowModel().rows.length === 0 && (
                  <tr>
                    <td
                      colSpan={columns.length}
                      className="px-4 py-8 text-center text-sm text-gray-500"
                    >
                      No crates available for this plant.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {selectedCrateIds.length} crate(s) selected
            </span>
            <button
              onClick={handleConfirmSelection}
              disabled={selectedCrateIds.length === 0 || selectMutation.isPending}
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {selectMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Confirm Selection
            </button>
          </div>

          {selectMutation.isError && (
            <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to confirm selection. Please try again.</span>
            </div>
          )}

          {selectMutation.isSuccess && (
            <div className="flex items-center gap-2 rounded-md border border-green-200 bg-green-50 p-4 text-green-700">
              <CheckCircle2 className="h-5 w-5" />
              <span>Selection confirmed successfully.</span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
