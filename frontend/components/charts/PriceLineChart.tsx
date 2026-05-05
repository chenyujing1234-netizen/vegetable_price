"use client";

import dynamic from "next/dynamic";
import type { EChartsOption } from "echarts";
import type { ForecastSeries, PriceSeries } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function PriceLineChart({
  series,
  forecast,
  height = 360,
}: {
  series: PriceSeries | undefined;
  forecast?: ForecastSeries;
  height?: number;
}) {
  if (!series) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground border rounded-md"
        style={{ height }}
      >
        加载中…
      </div>
    );
  }

  const histDates = series.points.map((p) => p.date);
  const histAvg = series.points.map((p) => Number(p.avg));
  const histLow = series.points.map((p) => (p.low === null ? null : Number(p.low)));
  const histHigh = series.points.map((p) => (p.high === null ? null : Number(p.high)));

  const fcDates = forecast?.points.map((p) => p.date) ?? [];
  const fcMean = forecast?.points.map((p) => Number(p.forecast)) ?? [];
  const fcLow95 = forecast?.points.map((p) => (p.lower_95 === null ? null : Number(p.lower_95))) ?? [];
  const fcHigh95 = forecast?.points.map((p) => (p.upper_95 === null ? null : Number(p.upper_95))) ?? [];

  const allDates = [...histDates, ...fcDates];
  const histAvgPadded = histAvg.concat(new Array(fcDates.length).fill(null));
  const histLowPadded = histLow.concat(new Array(fcDates.length).fill(null));
  const histHighPadded = histHigh.concat(new Array(fcDates.length).fill(null));
  const fcMeanPadded = new Array(histDates.length).fill(null).concat(fcMean);
  const fcLowPadded = new Array(histDates.length).fill(null).concat(fcLow95);
  const fcHighPadded = new Array(histDates.length).fill(null).concat(
    fcHigh95.map((h, i) => (h === null || fcLow95[i] === null ? null : h - (fcLow95[i] as number)))
  );

  const option: EChartsOption = {
    grid: { top: 50, right: 24, bottom: 60, left: 56 },
    tooltip: { trigger: "axis", axisPointer: { type: "cross" } },
    legend: {
      data: ["均价 (历史)", "最低-最高 (历史)", "预测均价", "95% 置信区间"].filter(Boolean),
      bottom: 8,
    },
    xAxis: { type: "category", data: allDates, boundaryGap: false },
    yAxis: { type: "value", name: "元/公斤", scale: true },
    dataZoom: [
      { type: "inside", start: 60, end: 100 },
      { type: "slider", height: 20, bottom: 30, start: 60, end: 100 },
    ],
    series: [
      {
        name: "最低-最高 (历史)",
        type: "line",
        stack: "range",
        data: histLowPadded,
        symbol: "none",
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        tooltip: { show: false },
      },
      {
        name: "最低-最高 (历史)",
        type: "line",
        stack: "range",
        data: histHighPadded.map((h, i) =>
          h === null || histLowPadded[i] === null ? null : h - (histLowPadded[i] as number)
        ),
        symbol: "none",
        lineStyle: { opacity: 0 },
        areaStyle: { color: "rgba(34,197,94,0.15)" },
      },
      {
        name: "均价 (历史)",
        type: "line",
        data: histAvgPadded,
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2, color: "#16a34a" },
        z: 5,
      },
      ...(forecast
        ? [
            {
              name: "95% 置信区间",
              type: "line" as const,
              stack: "fc",
              data: fcLowPadded,
              symbol: "none",
              lineStyle: { opacity: 0 },
              areaStyle: { opacity: 0 },
              tooltip: { show: false },
            },
            {
              name: "95% 置信区间",
              type: "line" as const,
              stack: "fc",
              data: fcHighPadded,
              symbol: "none",
              lineStyle: { opacity: 0 },
              areaStyle: { color: "rgba(59,130,246,0.18)" },
            },
            {
              name: "预测均价",
              type: "line" as const,
              data: fcMeanPadded,
              smooth: true,
              symbol: "none",
              lineStyle: { width: 2, color: "#2563eb", type: "dashed" },
              z: 6,
            },
          ]
        : []),
    ],
  };

  return <ReactECharts option={option} style={{ height }} notMerge />;
}
