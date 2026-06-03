import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import { StackedBarChart } from "@/components/charts/StackedBarChart";

interface DataPoint {
  tank_id: number;
  tank_name: string | null;
  crate_id: string | null;
  date: string;
  value: number | null;
}

interface Props {
  analysisType: "ml" | "msl" | "attribute";
  item: string;
  days?: number;
}

export function TankChartGrid({ analysisType, item, days = 30 }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["analysis", analysisType, item, days],
    queryFn: async () => {
      const res = await api.get(`/analysis/${analysisType}`, {
        params: { item, days },
      });
      return res.data.data as DataPoint[];
    },
    enabled: !!item,
  });

  if (isLoading) {
    return (
      <div className="py-8 text-center text-gray-500">Loading charts...</div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="py-8 text-center text-gray-500">No data available</div>
    );
  }

  // Group by tank
  const tankMap = new Map<number, { name: string; points: DataPoint[] }>();
  for (const pt of data) {
    if (!tankMap.has(pt.tank_id)) {
      tankMap.set(pt.tank_id, {
        name: pt.tank_name || `Tank ${pt.tank_id}`,
        points: [],
      });
    }
    tankMap.get(pt.tank_id)!.points.push(pt);
  }

  // For each tank, build chart data
  const charts = Array.from(tankMap.entries()).map(([tankId, { name, points }]) => {
    const dates = [...new Set(points.map((p) => p.date))].sort();
    const crates = [
      ...new Set(points.filter((p) => p.crate_id).map((p) => p.crate_id!)),
    ];

    const series = crates.map((crateId) => ({
      name: crateId,
      data: dates.map((d) => {
        const pt = points.find((p) => p.date === d && p.crate_id === crateId);
        return pt?.value ?? 0;
      }),
    }));

    return { tankId, name, dates, series };
  });

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {charts.map((chart) => (
        <div
          key={chart.tankId}
          className="rounded-lg border border-gray-200 bg-white p-4"
        >
          <StackedBarChart
            title={chart.name}
            xData={chart.dates}
            series={chart.series}
          />
        </div>
      ))}
    </div>
  );
}
