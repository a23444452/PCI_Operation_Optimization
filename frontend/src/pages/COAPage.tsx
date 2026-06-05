import { FileCheck, FileText, AlertCircle, CheckCircle2 } from "lucide-react";

export function COAPage() {
  const kpiCards = [
    { title: "Total COAs", value: "—", icon: FileText, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Approved", value: "—", icon: CheckCircle2, accent: "text-green-600", iconBg: "bg-green-50" },
    { title: "Pending Review", value: "—", icon: FileCheck, accent: "text-yellow-600", iconBg: "bg-yellow-50" },
    { title: "Issues Found", value: "—", icon: AlertCircle, accent: "text-red-600", iconBg: "bg-red-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">COA</h1>
        <p className="mt-1 text-sm text-gray-500">
          Certificate of Analysis management and tracking
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

      {/* Table Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">COA Records</h2>
          <div className="flex items-center gap-3">
            <select className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500">
              <option value="">All Status</option>
              <option value="approved">Approved</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">COA ID</th>
                  <th className="px-4 py-3">Product</th>
                  <th className="px-4 py-3">Batch</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Date</th>
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
