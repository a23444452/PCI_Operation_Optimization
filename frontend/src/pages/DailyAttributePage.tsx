import { Layers, TrendingUp, TrendingDown, PieChart } from "lucide-react";

export function DailyAttributePage() {
  const kpiCards = [
    { title: "Total Inspections", value: "—", icon: Layers, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Pass Rate", value: "—", icon: TrendingUp, accent: "text-green-600", iconBg: "bg-green-50" },
    { title: "Defect Rate", value: "—", icon: TrendingDown, accent: "text-red-600", iconBg: "bg-red-50" },
    { title: "Top Defect", value: "—", icon: PieChart, accent: "text-purple-600", iconBg: "bg-purple-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Daily Analysis — Attribute</h1>
        <p className="mt-1 text-sm text-gray-500">
          Attribute data daily analysis — pass/fail inspection metrics
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

      {/* Chart Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Pareto Chart</h2>
          <div className="flex items-center gap-3">
            <select className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500">
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </div>
        </div>
        <div className="flex items-center justify-center p-6 py-24">
          <div className="text-center text-gray-400">
            <PieChart className="mx-auto mb-3 h-12 w-12 opacity-40" />
            <p className="text-sm">Chart will be displayed once data is available.</p>
          </div>
        </div>
      </div>

      {/* Data Table Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Inspection Records</h2>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Date</th>
                  <th className="px-4 py-3">Attribute</th>
                  <th className="px-4 py-3">Inspected</th>
                  <th className="px-4 py-3">Defects</th>
                  <th className="px-4 py-3">Rate</th>
                </tr>
              </thead>
              <tbody className="text-gray-600">
                <tr>
                  <td colSpan={5} className="px-4 py-12 text-center text-gray-400">
                    No data available yet.
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
