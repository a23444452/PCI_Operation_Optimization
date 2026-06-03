import ReactEChartsCore from "echarts-for-react/lib/core";
import * as echarts from "echarts/core";
import { BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
]);

interface Series {
  name: string;
  data: number[];
}

interface Props {
  title: string;
  xData: string[];
  series: Series[];
  height?: number;
}

export function StackedBarChart({ title, xData, series, height = 300 }: Props) {
  const option = {
    title: { text: title, left: "center", textStyle: { fontSize: 14 } },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: "3%", right: "4%", bottom: "3%", containLabel: true },
    xAxis: { type: "category", data: xData },
    yAxis: { type: "value" },
    series: series.map((s) => ({
      name: s.name,
      type: "bar",
      stack: "total",
      data: s.data,
    })),
  };

  return (
    <ReactEChartsCore echarts={echarts} option={option} style={{ height }} />
  );
}
