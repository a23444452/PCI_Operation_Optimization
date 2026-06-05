import { Truck, Calendar, MapPin, BarChart3 } from "lucide-react";

export function ShippingPage() {
  const kpiCards = [
    { title: "Total Shipments", value: "—", icon: Truck, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Scheduled Today", value: "—", icon: Calendar, accent: "text-blue-600", iconBg: "bg-blue-50" },
    { title: "In Transit", value: "—", icon: MapPin, accent: "text-yellow-600", iconBg: "bg-yellow-50" },
    { title: "On-Time Rate", value: "—", icon: BarChart3, accent: "text-green-600", iconBg: "bg-green-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Shipping Assumption</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track shipping schedules, assumptions, and delivery performance
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
          <h2 className="text-lg font-semibold text-gray-800">Shipping Schedule</h2>
          <div className="flex items-center gap-2">
            <input
              type="date"
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            />
          </div>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-3">Shipment ID</th>
                  <th className="px-4 py-3">Destination</th>
                  <th className="px-4 py-3">ETA</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Crates</th>
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
