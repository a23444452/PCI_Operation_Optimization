import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ChevronDown, ChevronRight, Loader2 } from "lucide-react";
import api from "@/lib/api";

interface RiskCrate {
  id: number;
  crate_id: string;
  risk_level: "high" | "medium" | "low";
  rule_id: number | null;
  assessed_at: string;
  reason: string;
}

interface RiskRule {
  id: number;
  name: string;
  conditions_json: string;
  risk_level: "high" | "medium" | "low";
  is_active: boolean;
}

const RISK_BADGE: Record<string, string> = {
  high: "bg-red-100 text-red-800 border-red-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-green-100 text-green-800 border-green-200",
};

export function RiskPage() {
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [rulesExpanded, setRulesExpanded] = useState(false);

  const {
    data: crates,
    isLoading: cratesLoading,
    error: cratesError,
  } = useQuery<RiskCrate[]>({
    queryKey: ["risk-crates", levelFilter],
    queryFn: async () => {
      const res = await api.get("/risk/crates", { params: { level: levelFilter } });
      return res.data.data;
    },
  });

  const { data: rules, isLoading: rulesLoading } = useQuery<RiskRule[]>({
    queryKey: ["risk-rules"],
    queryFn: async () => {
      const res = await api.get("/risk/rules");
      return res.data.data;
    },
  });

  const activeRules = rules?.filter((r) => r.is_active) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Risk Management</h2>
      </div>

      <div className="flex items-center gap-4">
        <label htmlFor="level-filter" className="text-sm font-medium text-gray-700">
          Risk Level:
        </label>
        <select
          id="level-filter"
          value={levelFilter}
          onChange={(e) => setLevelFilter(e.target.value)}
          className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="all">All Levels</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {cratesLoading && (
        <div className="flex items-center gap-2 text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading risk assessments...</span>
        </div>
      )}

      {cratesError && (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>Failed to load risk data. Please try again.</span>
        </div>
      )}

      {crates && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Crate ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Risk Level
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Assessed At
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Reason
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {crates.map((crate) => (
                <tr key={crate.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm font-mono text-gray-900">
                    {crate.crate_id}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm">
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${RISK_BADGE[crate.risk_level] ?? ""}`}
                    >
                      {crate.risk_level}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-600">
                    {crate.assessed_at}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {crate.reason}
                  </td>
                </tr>
              ))}
              {crates.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-sm text-gray-500">
                    No risk assessments found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="rounded-lg border border-gray-200 shadow-sm">
        <button
          onClick={() => setRulesExpanded(!rulesExpanded)}
          className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          {rulesExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          Active Risk Rules ({activeRules.length})
        </button>

        {rulesExpanded && (
          <div className="border-t border-gray-200">
            {rulesLoading && (
              <div className="flex items-center gap-2 p-4 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Loading rules...</span>
              </div>
            )}
            {activeRules.length === 0 && !rulesLoading && (
              <p className="p-4 text-sm text-gray-500">No active rules configured.</p>
            )}
            {activeRules.length > 0 && (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      Name
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      Risk Level
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium uppercase text-gray-500">
                      Conditions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {activeRules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-900">{rule.name}</td>
                      <td className="px-4 py-2 text-sm">
                        <span
                          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${RISK_BADGE[rule.risk_level] ?? ""}`}
                        >
                          {rule.risk_level}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm font-mono text-gray-600">
                        {rule.conditions_json}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
