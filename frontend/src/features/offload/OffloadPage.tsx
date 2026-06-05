import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  CheckCircle2,
  XCircle,
  Loader2,
  AlertCircle,
  Search,
} from "lucide-react";
import api from "@/lib/api";
import { usePlants } from "./usePlants";

function getDefaultDates() {
  const today = new Date();
  const twoDaysAgo = new Date(today);
  twoDaysAgo.setDate(today.getDate() - 2);
  const oneDayAgo = new Date(today);
  oneDayAgo.setDate(today.getDate() - 1);
  const fmt = (d: Date) => d.toISOString().slice(0, 10);
  return { start: fmt(twoDaysAgo), end: fmt(oneDayAgo) };
}

interface EvaluationItem {
  crate_id: string;
  in_qty: number;
  is_compliant: boolean;
  failed_criteria: string[];
}

interface PipelineResult {
  receiver_specs: Record<string, Record<string, unknown>[]>;
  general_spec: Record<string, unknown>[];
  solid_density: Record<string, unknown>[];
  attribute: Record<string, unknown>[];
  evaluation: Record<string, EvaluationItem[]>;
  summary: Record<string, number>;
}

function DataTable({ data, title }: { data: Record<string, unknown>[]; title: string }) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 text-center text-sm text-gray-500">
        No data available for {title}.
      </div>
    );
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="whitespace-nowrap px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="whitespace-nowrap px-3 py-2 text-gray-900">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function OffloadPage() {
  const [plantId, setPlantId] = useState<string>("");
  const defaults = getDefaultDates();
  const [startDate, setStartDate] = useState(defaults.start);
  const [endDate, setEndDate] = useState(defaults.end);
  const [selectedPlants, setSelectedPlants] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string>("general_spec");
  const [activeReceiverSpec, setActiveReceiverSpec] = useState<string>("");

  const { data: plants } = usePlants();

  useEffect(() => {
    if (plants && plants.length > 0 && selectedPlants.length === 0) {
      setSelectedPlants(plants.map((p) => p.code));
    }
  }, [plants]);

  const pipelineMutation = useMutation<PipelineResult>({
    mutationFn: async () => {
      const res = await api.get("/offload/pipeline", {
        params: {
          start_date: startDate,
          end_date: endDate,
          plants: selectedPlants.join(","),
        },
      });
      return res.data.data;
    },
    onSuccess: (data) => {
      const specNames = Object.keys(data.receiver_specs);
      if (specNames.length > 0 && !activeReceiverSpec) {
        setActiveReceiverSpec(specNames[0]);
      }
    },
  });

  function handleRunPipeline() {
    pipelineMutation.mutate();
  }

  const pipelineData = pipelineMutation.data;
  const specNames = pipelineData ? Object.keys(pipelineData.receiver_specs) : [];

  const tabs = [
    { key: "general_spec", label: "General Spec" },
    { key: "receiver_specs", label: "Receiver Specs" },
    { key: "solid_density", label: "SOLID Density" },
    { key: "attribute", label: "Attribute" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">PCI Offload Selection</h2>
      </div>

      {/* Pipeline Query Section */}
      <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">Data Pipeline Query</h3>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="mt-1 rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <span className="block text-sm font-medium text-gray-700">Plant</span>
            <div className="mt-1 flex gap-3">
              {(plants ?? []).map((plant) => (
                <label key={plant.code} className="inline-flex items-center gap-1.5 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedPlants.includes(plant.code)}
                    onChange={(e) => {
                      setSelectedPlants((prev) =>
                        e.target.checked ? [...prev, plant.code] : prev.filter((p) => p !== plant.code)
                      );
                    }}
                    className="h-4 w-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500"
                  />
                  {plant.code}
                </label>
              ))}
            </div>
          </div>
          <button
            onClick={handleRunPipeline}
            disabled={pipelineMutation.isPending || selectedPlants.length === 0}
            className="inline-flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pipelineMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {pipelineMutation.isPending ? "Querying..." : "Run Pipeline"}
          </button>
        </div>

        {pipelineMutation.isError && (
          <div className="mt-4 flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm">
              Pipeline failed: {(pipelineMutation.error as Error)?.message ?? "Unknown error"}
            </span>
          </div>
        )}

        {pipelineMutation.isPending && (
          <div className="mt-4 flex items-center gap-2 text-gray-500">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">
              Running pipeline (fetching from MESDW, Oracle, Cube)... This may take 30-60 seconds.
            </span>
          </div>
        )}
      </div>

      {/* Pipeline Results */}
      {pipelineData && (
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-5 py-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">
                Pipeline Results ({startDate} ~ {endDate})
              </h3>
              <div className="text-xs text-gray-500">
                General: {pipelineData.summary.general_rows} rows |
                Specs: {pipelineData.summary.total_specs} |
                Attribute: {pipelineData.summary.attribute_rows} rows
              </div>
            </div>

            {/* Tabs */}
            <div className="mt-3 flex gap-1 border-b border-gray-100">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`rounded-t-md px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? "border-b-2 border-cyan-600 text-cyan-700"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-5">
            {activeTab === "general_spec" && (
              <DataTable data={pipelineData.general_spec} title="General Spec" />
            )}

            {activeTab === "solid_density" && (
              <DataTable data={pipelineData.solid_density} title="SOLID Density" />
            )}

            {activeTab === "attribute" && (
              <DataTable data={pipelineData.attribute} title="Attribute" />
            )}

            {activeTab === "receiver_specs" && (
              <div className="space-y-4">
                {specNames.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {specNames.map((spec) => (
                      <button
                        key={spec}
                        onClick={() => setActiveReceiverSpec(spec)}
                        className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                          activeReceiverSpec === spec
                            ? "bg-cyan-100 text-cyan-800"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        {spec} ({pipelineData.receiver_specs[spec]?.length ?? 0})
                      </button>
                    ))}
                  </div>
                )}
                {activeReceiverSpec && pipelineData.receiver_specs[activeReceiverSpec] && (
                  <DataTable
                    data={pipelineData.receiver_specs[activeReceiverSpec]}
                    title={activeReceiverSpec}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Crate Evaluation Section — uses pipeline evaluation results */}
      {pipelineData?.evaluation && (
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h3 className="mb-4 text-lg font-semibold text-gray-800">Crate Evaluation</h3>
          <div className="flex items-center gap-4 mb-4">
            <label htmlFor="eval-plant-select" className="text-sm font-medium text-gray-700">
              Plant:
            </label>
            <select
              id="eval-plant-select"
              value={plantId}
              onChange={(e) => setPlantId(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">Select a plant...</option>
              {(plants ?? []).map((p) => (
                <option key={p.code} value={p.code}>{p.code}</option>
              ))}
            </select>
          </div>

          {plantId && (() => {
            const matchingSpecs = Object.entries(pipelineData.evaluation)
              .filter(([specName]) => specName.startsWith(plantId));
            const allItems = matchingSpecs.flatMap(([specName, items]) =>
              items.map((item) => ({ ...item, spec_name: specName }))
            );
            const compliantCount = allItems.filter((i) => i.is_compliant).length;

            return (
              <div className="space-y-3">
                <div className="flex gap-4 text-sm">
                  <span className="text-gray-600">
                    Total: <strong>{allItems.length}</strong> crates
                  </span>
                  <span className="text-green-700">
                    Compliant: <strong>{compliantCount}</strong>
                  </span>
                  <span className="text-red-700">
                    Non-compliant: <strong>{allItems.length - compliantCount}</strong>
                  </span>
                </div>
                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Spec</th>
                        <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Crate ID</th>
                        <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">In Qty</th>
                        <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Status</th>
                        <th className="px-3 py-2 text-left text-xs font-medium uppercase text-gray-500">Failed Criteria</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {allItems.map((item, idx) => (
                        <tr
                          key={`${item.spec_name}-${item.crate_id}-${idx}`}
                          className={item.is_compliant ? "hover:bg-gray-50" : "bg-red-50/30 hover:bg-red-50/50"}
                        >
                          <td className="whitespace-nowrap px-3 py-2 text-gray-600">{item.spec_name}</td>
                          <td className="whitespace-nowrap px-3 py-2 font-mono">{item.crate_id}</td>
                          <td className="whitespace-nowrap px-3 py-2">{item.in_qty}</td>
                          <td className="whitespace-nowrap px-3 py-2">
                            {item.is_compliant ? (
                              <CheckCircle2 className="h-5 w-5 text-green-600" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500" />
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {item.failed_criteria.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {item.failed_criteria.map((c) => (
                                  <span key={c} className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                                    {c}
                                  </span>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                      {allItems.length === 0 && (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                            No evaluation data for this plant.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
