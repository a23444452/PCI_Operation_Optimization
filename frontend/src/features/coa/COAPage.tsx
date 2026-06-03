import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import {
  Loader2,
  AlertCircle,
  Download,
  ArrowUpDown,
  ShieldAlert,
} from "lucide-react";
import api from "@/lib/api";
import { usePlants } from "@/features/offload/usePlants";

interface DefectRatios {
  [type: string]: number;
}

interface COARecord {
  crate_id: string;
  batch_id: string;
  in_qty: number;
  cut_lot_end_date: string;
  defect_ratios: DefectRatios;
  msl: Record<string, number>;
  is_override: boolean;
}

const columnHelper = createColumnHelper<COARecord>();

export function COAPage() {
  const [plantId, setPlantId] = useState<number | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [isExporting, setIsExporting] = useState(false);

  const { data: plants, isLoading: plantsLoading } = usePlants();

  const {
    data: records,
    isLoading: recordsLoading,
    error: recordsError,
  } = useQuery<COARecord[]>({
    queryKey: ["coa-data", plantId],
    queryFn: async () => {
      const res = await api.get("/coa/data", { params: { plant_id: plantId } });
      return res.data.data;
    },
    enabled: plantId !== null,
  });

  const defectTypes = useMemo(() => {
    if (!records || records.length === 0) return [];
    const types = new Set<string>();
    for (const r of records) {
      for (const key of Object.keys(r.defect_ratios)) {
        types.add(key);
      }
    }
    return Array.from(types).sort();
  }, [records]);

  const mslKeys = useMemo(() => {
    if (!records || records.length === 0) return [];
    const keys = new Set<string>();
    for (const r of records) {
      for (const key of Object.keys(r.msl)) {
        keys.add(key);
      }
    }
    return Array.from(keys).sort();
  }, [records]);

  const columns = useMemo(
    () => [
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
      ...defectTypes.map((type) =>
        columnHelper.display({
          id: `defect_${type}`,
          header: type,
          cell: ({ row }) => {
            const ratio = row.original.defect_ratios[type];
            if (ratio === undefined) return <span className="text-gray-300">-</span>;
            return <span className="text-sm">{(ratio * 100).toFixed(2)}%</span>;
          },
        })
      ),
      ...mslKeys.map((key) =>
        columnHelper.display({
          id: `msl_${key}`,
          header: `MSL ${key}`,
          cell: ({ row }) => {
            const val = row.original.msl[key];
            if (val === undefined) return <span className="text-gray-300">-</span>;
            return <span className="text-sm">{val.toFixed(3)}</span>;
          },
        })
      ),
      columnHelper.accessor("is_override", {
        header: "Override",
        cell: (info) =>
          info.getValue() ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
              <ShieldAlert className="h-3 w-3" />
              Override
            </span>
          ) : (
            <span className="text-gray-400">-</span>
          ),
      }),
    ],
    [defectTypes, mslKeys]
  );

  const table = useReactTable({
    data: records ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getRowId: (row) => row.crate_id,
  });

  async function handleExport() {
    if (plantId === null) return;
    setIsExporting(true);
    try {
      const res = await api.get("/coa/export", {
        params: { plant_id: plantId },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `coa_export_plant_${plantId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">COA</h2>
        {plantId !== null && (
          <button
            onClick={handleExport}
            disabled={isExporting || recordsLoading}
            className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isExporting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            Export Excel
          </button>
        )}
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
        <p className="text-sm text-gray-500">Select a plant to view COA data.</p>
      )}

      {recordsLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading COA data...</span>
        </div>
      )}

      {recordsError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load COA data. Please try again.</span>
        </div>
      )}

      {records && (
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
                  className={row.original.is_override ? "bg-amber-50/30 hover:bg-amber-50/50" : "hover:bg-gray-50"}
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
              ))}
              {table.getRowModel().rows.length === 0 && (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-4 py-8 text-center text-sm text-gray-500"
                  >
                    No COA data available for this plant.
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
