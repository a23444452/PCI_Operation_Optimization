import { useState } from "react";
import { Database, Upload, Download, RefreshCw } from "lucide-react";

const tabs = [
  { id: "plants", label: "Plants" },
  { id: "tanks", label: "Tanks" },
  { id: "products", label: "Products" },
  { id: "import", label: "Import" },
  { id: "export", label: "Export" },
];

export function DataManagementPage() {
  const [activeTab, setActiveTab] = useState("plants");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Data Management</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage plants, tanks, products, and data import/export
        </p>
      </div>

      {/* Tabs */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100">
          <nav className="flex gap-0 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "border-cyan-500 text-cyan-600"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === "plants" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <input
                  type="text"
                  placeholder="Search plants..."
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                <button className="rounded-md bg-cyan-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
                  Add Plant
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-4 py-3">Name</th>
                      <th className="px-4 py-3">Code</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-600">
                    <tr>
                      <td colSpan={4} className="px-4 py-12 text-center text-gray-400">
                        No data available yet.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "tanks" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <input
                  type="text"
                  placeholder="Search tanks..."
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                <button className="rounded-md bg-cyan-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
                  Add Tank
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-4 py-3">Tank Name</th>
                      <th className="px-4 py-3">Plant</th>
                      <th className="px-4 py-3">Capacity</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-600">
                    <tr>
                      <td colSpan={4} className="px-4 py-12 text-center text-gray-400">
                        No data available yet.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "products" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <input
                  type="text"
                  placeholder="Search products..."
                  className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                />
                <button className="rounded-md bg-cyan-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
                  Add Product
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-100 text-xs font-medium uppercase tracking-wider text-gray-500">
                      <th className="px-4 py-3">Product Name</th>
                      <th className="px-4 py-3">Code</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-600">
                    <tr>
                      <td colSpan={4} className="px-4 py-12 text-center text-gray-400">
                        No data available yet.
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "import" && (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
                <Upload className="mx-auto mb-4 h-10 w-10 text-gray-400" />
                <p className="text-sm font-medium text-gray-700">
                  Drag & drop files here, or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-400">
                  Supports .xlsx, .csv files
                </p>
                <button className="mt-4 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
                  Select File
                </button>
              </div>
            </div>
          )}

          {activeTab === "export" && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">Select data to export:</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {["Plants", "Tanks", "Products", "Offload History", "Shipping Log", "Risk Assessments"].map((item) => (
                  <label key={item} className="flex items-center gap-3 rounded-lg border border-gray-200 p-4 cursor-pointer hover:bg-gray-50 transition-colors">
                    <input type="checkbox" className="h-4 w-4 rounded border-gray-300 text-cyan-600 focus:ring-cyan-500" />
                    <span className="text-sm font-medium text-gray-700">{item}</span>
                  </label>
                ))}
              </div>
              <button className="flex items-center gap-2 rounded-md bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-700 transition-colors">
                <Download className="h-4 w-4" />
                Export Selected
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
