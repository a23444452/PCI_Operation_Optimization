import { useState } from "react";
import { Package, Clock, CheckCircle, AlertTriangle } from "lucide-react";

export function OffloadPage() {
  const [plant, setPlant] = useState("");

  const kpiCards = [
    { title: "Total Crates", value: "—", icon: Package, accent: "text-cyan-600", iconBg: "bg-cyan-50" },
    { title: "Pending Offload", value: "—", icon: Clock, accent: "text-yellow-600", iconBg: "bg-yellow-50" },
    { title: "Completed", value: "—", icon: CheckCircle, accent: "text-green-600", iconBg: "bg-green-50" },
    { title: "At Risk", value: "—", icon: AlertTriangle, accent: "text-red-600", iconBg: "bg-red-50" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">PCI Offload</h1>
        <p className="mt-1 text-sm text-gray-500">
          Monitor and manage crate offload operations across plants
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

      {/* Crate List Table Card */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">Crate List</h2>
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-500">Plant:</label>
            <select
              value={plant}
              onChange={(e) => setPlant(e.target.value)}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              <option value="">Select a plant...</option>
              <option value="TP3">TP3</option>
              <option value="TK3">TK3</option>
              <option value="TC3">TC3</option>
            </select>
          </div>
        </div>
        <div className="p-6">
          {!plant ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-400">
              <Package className="mb-3 h-12 w-12 opacity-40" />
              <p className="text-sm">Select a plant to view available crates.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50 text-xs font-medium uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-3">Crate ID</th>
                    <th className="px-4 py-3">Tank</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Priority</th>
                    <th className="px-4 py-3 text-center" colSpan={3}>
                      <span className="block border-b border-gray-300 pb-1 mb-1">Daily Analysis</span>
                      <div className="flex">
                        <span className="flex-1 text-center">Attribute</span>
                        <span className="flex-1 text-center">ML</span>
                        <span className="flex-1 text-center">MSL</span>
                      </div>
                    </th>
                    <th className="px-4 py-3">Last Updated</th>
                  </tr>
                </thead>
                <tbody className="text-gray-600">
                  <tr className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">CRT-2024-001</td>
                    <td className="px-4 py-3">Tank A1</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-700">
                        Pending
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">
                        High
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                        Fail
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">2024-06-03 14:30</td>
                  </tr>
                  <tr className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">CRT-2024-002</td>
                    <td className="px-4 py-3">Tank B2</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                        Completed
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                        Normal
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">2024-06-03 12:15</td>
                  </tr>
                  <tr className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">CRT-2024-003</td>
                    <td className="px-4 py-3">Tank A3</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-700">
                        Pending
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-700">
                        Medium
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                        Fail
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-700">
                        Warning
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Pass
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500">2024-06-03 10:45</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
