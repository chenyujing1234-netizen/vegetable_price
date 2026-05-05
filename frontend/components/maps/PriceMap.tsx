"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { PriceHeatPoint } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

/**
 * 价格地图。
 *
 * 实现说明：ECharts 在 5.x 之后不再内置中国 GeoJSON，需要 registerMap。
 * 为减少依赖，这里用 scatter on 二维坐标（X=经度, Y=纬度）+ 自定义网格 +
 * 大致的中国边界作为背景。生产环境可替换为高德地图 JS API（已预留 KEY）。
 */
export default function PriceMap({ points }: { points: PriceHeatPoint[] }) {
  const data = points
    .filter((p) => p.lng != null && p.lat != null)
    .map((p) => ({
      name: p.market_name,
      value: [p.lng as number, p.lat as number, p.avg],
      yoy: p.yoy,
    }));

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-muted-foreground border rounded-md h-[520px]">
        暂无市场坐标数据
      </div>
    );
  }

  const max = Math.max(...data.map((d) => d.value[2] as number), 1);
  const min = Math.min(...data.map((d) => d.value[2] as number), 0);

  const option: EChartsOption = {
    tooltip: {
      trigger: "item",
      formatter: (p: any) =>
        `<strong>${p.name}</strong><br/>均价：¥${(p.value[2] as number).toFixed(2)}/公斤<br/>同比：${
          p.data.yoy != null ? `${p.data.yoy > 0 ? "+" : ""}${p.data.yoy.toFixed(1)}%` : "—"
        }`,
    },
    visualMap: {
      min: Math.floor(min),
      max: Math.ceil(max),
      calculable: true,
      inRange: { color: ["#16a34a", "#fbbf24", "#ef4444"] },
      text: ["高", "低"],
      left: 10,
      bottom: 10,
    },
    grid: { top: 30, right: 30, bottom: 60, left: 60 },
    xAxis: {
      type: "value",
      name: "经度 °E",
      min: 73,
      max: 135,
      splitNumber: 8,
      splitLine: { show: true, lineStyle: { color: "#e5e7eb", type: "dashed" } },
    },
    yAxis: {
      type: "value",
      name: "纬度 °N",
      min: 18,
      max: 53,
      splitNumber: 7,
      splitLine: { show: true, lineStyle: { color: "#e5e7eb", type: "dashed" } },
    },
    series: [
      {
        type: "scatter",
        symbolSize: (val: number[]) => 16 + ((val[2] - min) / (max - min || 1)) * 24,
        data,
        label: {
          show: true,
          position: "right",
          formatter: (p: any) => p.name,
          fontSize: 11,
          color: "#475569",
        },
        emphasis: { label: { show: true, color: "#0f172a", fontWeight: "bold" } },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 520 }} notMerge opts={{ renderer: "canvas" }} />;
}
