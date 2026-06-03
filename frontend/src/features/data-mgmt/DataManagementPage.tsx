import { useState } from "react";
import { CrudTable } from "./CrudTable";

const TABS = [
  {
    key: "plants",
    label: "Plants",
    endpoint: "/plants",
    columns: [
      { key: "name", label: "Name", type: "text" as const },
      { key: "code", label: "Code", type: "text" as const },
      { key: "location", label: "Location", type: "text" as const },
    ],
    createFields: [
      { key: "name", label: "Name", type: "text" as const },
      { key: "code", label: "Code", type: "text" as const },
      { key: "location", label: "Location", type: "text" as const },
    ],
  },
  {
    key: "plant-criteria",
    label: "Plant Criteria",
    endpoint: "/plant-criteria",
    columns: [
      { key: "plant_id", label: "Plant ID", type: "number" as const },
      { key: "defect_type", label: "Defect Type", type: "text" as const },
      { key: "threshold", label: "Threshold", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
    createFields: [
      { key: "plant_id", label: "Plant ID", type: "number" as const },
      { key: "defect_type", label: "Defect Type", type: "text" as const },
      { key: "threshold", label: "Threshold", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
  },
  {
    key: "tanks",
    label: "Tanks",
    endpoint: "/tanks",
    columns: [
      { key: "tank_name", label: "Tank Name", type: "text" as const },
      { key: "plant_id", label: "Plant ID", type: "number" as const },
      { key: "capacity", label: "Capacity", type: "number" as const },
    ],
    createFields: [
      { key: "tank_name", label: "Tank Name", type: "text" as const },
      { key: "plant_id", label: "Plant ID", type: "number" as const },
      { key: "capacity", label: "Capacity", type: "number" as const },
    ],
  },
  {
    key: "ml-items",
    label: "ML Items",
    endpoint: "/ml-items",
    columns: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
    createFields: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
  },
  {
    key: "msl-items",
    label: "MSL Items",
    endpoint: "/msl-items",
    columns: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
    createFields: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
  },
  {
    key: "attribute-items",
    label: "Attribute Items",
    endpoint: "/attribute-items",
    columns: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
    createFields: [
      { key: "item_name", label: "Item Name", type: "text" as const },
      { key: "category", label: "Category", type: "text" as const },
      { key: "spec_limit", label: "Spec Limit", type: "number" as const },
      { key: "is_active", label: "Active", type: "boolean" as const },
    ],
  },
];

export function DataManagementPage() {
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const currentTab = TABS.find((t) => t.key === activeTab) ?? TABS[0];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Data Management</h2>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-6 overflow-x-auto" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium ${
                activeTab === tab.key
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <CrudTable
        key={currentTab.key}
        title={currentTab.label}
        endpoint={currentTab.endpoint}
        columns={currentTab.columns}
        createFields={currentTab.createFields}
      />
    </div>
  );
}
