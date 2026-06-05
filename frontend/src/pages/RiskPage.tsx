import { ShieldAlert, ShieldCheck, AlertTriangle, Activity } from "lucide-react";

export function RiskPage() {
  const kpiCards = [
    { title: "Total Assessments", value: "—", icon: Activity, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Low Risk", value: "—", icon: ShieldCheck, accent: "text-green-600", iconBg: "bg-green-50" },
    { title: "Medium Risk", value: "—", icon: AlertTriangle, accent: "text-yellow-600", iconBg: "bg-yellow-50" },
    { title: "High Risk", value: "—", icon: ShieldAlert, accent: "text-red-600", iconBg: "bg-red-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Risk Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Assess and manage risk levels across crates and production lines
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

      {/* Risk Rules Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Risk Rules</h2>
          <button className="rounded-md bg-cyan-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
            Add Rule
          </button>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Rule Name</th>
                  <th className="px-4 py-3">Conditions</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-gray-400">
                    No rules configured yet.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Assessments Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Recent Assessments</h2>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Crate ID</th>
                  <th className="px-4 py-3">Risk Level</th>
                  <th className="px-4 py-3">Matched Rule</th>
                  <th className="px-4 py-3">Assessed At</th>
                  <th className="px-4 py-3">Reason</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-gray-400">
                    No assessments recorded yet.
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
