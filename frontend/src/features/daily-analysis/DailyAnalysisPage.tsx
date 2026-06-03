import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { TankChartGrid } from "./TankChartGrid";

interface Props {
  analysisType: "ml" | "msl" | "attribute";
  title: string;
}

export function DailyAnalysisPage({ analysisType, title }: Props) {
  const [selectedItem, setSelectedItem] = useState("");
  const [days, setDays] = useState(30);

  const { data: items } = useQuery({
    queryKey: ["analysis-items", analysisType],
    queryFn: async () => {
      const res = await api.get(`/analysis/items/${analysisType}`);
      return res.data.data as {
        id: number;
        name: string;
        display_name: string | null;
      }[];
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
        <div className="flex items-center gap-4">
          <select
            value={selectedItem}
            onChange={(e) => setSelectedItem(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="">Select item...</option>
            {items?.map((item) => (
              <option key={item.id} value={item.name}>
                {item.display_name || item.name}
              </option>
            ))}
          </select>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {selectedItem ? (
        <TankChartGrid analysisType={analysisType} item={selectedItem} days={days} />
      ) : (
        <div className="py-16 text-center text-gray-400">
          Select an item to view charts
        </div>
      )}
    </div>
  );
}
