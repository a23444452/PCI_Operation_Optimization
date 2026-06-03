import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getExpandedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import {
  ChevronRight,
  ChevronDown,
  Loader2,
  AlertCircle,
  RefreshCw,
  ArrowUpDown,
} from "lucide-react";
import api from "@/lib/api";
import { usePlants } from "@/features/offload/usePlants";

interface Schedule {
  id: number;
  plant_id: number;
  plant_name: string;
  target_qty: number;
  ship_date: string;
  source_file: string;
  assigned_qty: number;
  assignment_count: number;
}

interface Assignment {
  id: number;
  crate_id: string;
  priority_order: number;
  in_qty: number;
  cut_lot_end_date: string;
}

const columnHelper = createColumnHelper<Schedule>();

export function ShippingPage() {
  const queryClient = useQueryClient();
  const [plantId, setPlantId] = useState<number | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data: plants, isLoading: plantsLoading } = usePlants();

  const {
    data: schedules,
    isLoading: schedulesLoading,
    error: schedulesError,
  } = useQuery<Schedule[]>({
    queryKey: ["shipping-schedules", plantId],
    queryFn: async () => {
      const res = await api.get("/shipping/schedules", { params: { plant_id: plantId } });
      return res.data.data;
    },
    enabled: plantId !== null,
  });

  const {
    data: assignments,
    isLoading: assignmentsLoading,
  } = useQuery<Assignment[]>({
    queryKey: ["shipping-assignments", expandedId],
    queryFn: async () => {
      const res = await api.get(`/shipping/schedules/${expandedId}/assignments`);
      return res.data.data;
    },
    enabled: expandedId !== null,
  });

  const recalculateMutation = useMutation({
    mutationFn: async (scheduleId: number) => {
      const res = await api.post("/shipping/recalculate", { schedule_id: scheduleId });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shipping-schedules", plantId] });
      if (expandedId !== null) {
        queryClient.invalidateQueries({ queryKey: ["shipping-assignments", expandedId] });
      }
    },
  });

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: "expand",
        header: "",
        cell: ({ row }) => (
          <button
            onClick={() => setExpandedId(expandedId === row.original.id ? null : row.original.id)}
            className="rounded p-1 hover:bg-gray-100"
          >
            {expandedId === row.original.id ? (
              <ChevronDown className="h-4 w-4 text-gray-600" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-600" />
            )}
          </button>
        ),
      }),
      columnHelper.accessor("ship_date", {
        header: "Ship Date",
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor("plant_name", {
        header: "Plant",
        cell: (info) => info.getValue(),
      }),
      columnHelper.accessor("target_qty", {
        header: "Target Qty",
        cell: (info) => info.getValue().toLocaleString(),
      }),
      columnHelper.accessor("assigned_qty", {
        header: "Assigned Qty",
        cell: (info) => info.getValue().toLocaleString(),
      }),
      columnHelper.display({
        id: "fulfillment",
        header: "Fulfillment",
        cell: ({ row }) => {
          const target = row.original.target_qty;
          const assigned = row.original.assigned_qty;
          const pct = target > 0 ? Math.min((assigned / target) * 100, 100) : 0;
          const color =
            pct >= 100 ? "bg-green-500" : pct >= 75 ? "bg-blue-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500";
          return (
            <div className="flex items-center gap-2">
              <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-600">{pct.toFixed(0)}%</span>
            </div>
          );
        },
      }),
      columnHelper.accessor("assignment_count", {
        header: "Assignments",
        cell: (info) => info.getValue(),
      }),
      columnHelper.display({
        id: "actions",
        header: "",
        cell: ({ row }) => (
          <button
            onClick={(e) => {
              e.stopPropagation();
              recalculateMutation.mutate(row.original.id);
            }}
            disabled={recalculateMutation.isPending}
            className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 disabled:opacity-50"
            title="Recalculate assignments"
          >
            <RefreshCw
              className={`h-3 w-3 ${recalculateMutation.isPending ? "animate-spin" : ""}`}
            />
            Recalculate
          </button>
        ),
      }),
    ],
    [expandedId, recalculateMutation]
  );

  const table = useReactTable({
    data: schedules ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowId: (row) => String(row.id),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Shipping Assumption</h2>
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
            setExpandedId(null);
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
        <p className="text-sm text-gray-500">Select a plant to view shipping schedules.</p>
      )}

      {schedulesLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading schedules...</span>
        </div>
      )}

      {schedulesError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load schedules. Please try again.</span>
        </div>
      )}

      {schedules && (
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
                <>
                  <tr
                    key={row.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() =>
                      setExpandedId(expandedId === row.original.id ? null : row.original.id)
                    }
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td
                        key={cell.id}
                        className="whitespace-nowrap px-4 py-3 text-sm text-gray-900"
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                  {expandedId === row.original.id && (
                    <tr key={`${row.id}-expanded`}>
                      <td colSpan={columns.length} className="bg-gray-50 px-8 py-4">
                        <AssignmentDetails
                          assignments={assignments ?? []}
                          isLoading={assignmentsLoading}
                        />
                      </td>
                    </tr>
                  )}
                </>
              ))}
              {table.getRowModel().rows.length === 0 && (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-4 py-8 text-center text-sm text-gray-500"
                  >
                    No schedules available for this plant.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {recalculateMutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Recalculation failed. Please try again.</span>
        </div>
      )}
    </div>
  );
}

function AssignmentDetails({
  assignments,
  isLoading,
}: {
  assignments: Assignment[];
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm">Loading assignments...</span>
      </div>
    );
  }

  if (assignments.length === 0) {
    return <p className="text-sm text-gray-500">No assignments for this schedule.</p>;
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-gray-700">Assignment Details</h4>
      <table className="min-w-full divide-y divide-gray-200 rounded border border-gray-200">
        <thead className="bg-white">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
              Priority
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
              Crate ID
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
              In Qty
            </th>
            <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">
              Cut Lot End Date
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {assignments.map((a) => (
            <tr key={a.id} className="hover:bg-gray-50">
              <td className="px-3 py-2 text-sm text-gray-900">{a.priority_order}</td>
              <td className="px-3 py-2 font-mono text-sm text-gray-900">{a.crate_id}</td>
              <td className="px-3 py-2 text-sm text-gray-900">{a.in_qty.toLocaleString()}</td>
              <td className="px-3 py-2 text-sm text-gray-900">{a.cut_lot_end_date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
