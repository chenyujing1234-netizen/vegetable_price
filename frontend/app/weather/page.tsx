"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/PageHeader";
import { type Market, type WeatherSeries, useApi } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export default function WeatherPage() {
  const { data: markets } = useApi<Market[]>("/api/markets");
  const origins = markets?.filter((m) => m.is_origin) ?? [];
  const [region, setRegion] = useState<string | null>(null);
  const activeRegion = region ?? origins[0]?.region_code ?? null;

  const { data: series } = useApi<WeatherSeries>(
    activeRegion ? `/api/weather/series?region_code=${activeRegion}&days=365` : null
  );

  const dates = series?.points.map((p) => p.date) ?? [];
  const temps = series?.points.map((p) => p.temp_avg) ?? [];
  const tempsMax = series?.points.map((p) => p.temp_max) ?? [];
  const tempsMin = series?.points.map((p) => p.temp_min) ?? [];
  const precip = series?.points.map((p) => p.precip) ?? [];

  return (
    <div>
      <PageHeader title="天气数据" description="主产区近 365 天气温/降水时序，用作价格预测外生变量" />

      <div className="flex gap-3 mb-4">
        <select
          className="text-sm border rounded-md px-3 py-1.5 bg-background"
          value={activeRegion ?? ""}
          onChange={(e) => setRegion(e.target.value)}
        >
          {origins.map((m) => (
            <option key={m.region_code} value={m.region_code}>
              {m.name.replace(/[（(].*$/, "")}
            </option>
          ))}
        </select>
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>{series?.region_name ?? "—"} 气温变化</CardTitle>
        </CardHeader>
        <CardContent>
          <ReactECharts
            style={{ height: 320 }}
            notMerge
            option={{
              tooltip: { trigger: "axis" },
              legend: { data: ["平均", "最高", "最低"], bottom: 0 },
              grid: { top: 30, right: 24, bottom: 50, left: 50 },
              xAxis: { type: "category", data: dates, boundaryGap: false },
              yAxis: { type: "value", name: "℃" },
              dataZoom: [{ type: "inside", start: 60, end: 100 }],
              series: [
                { name: "最高", type: "line", data: tempsMax, smooth: true, symbol: "none", lineStyle: { color: "#ef4444" } },
                { name: "平均", type: "line", data: temps, smooth: true, symbol: "none", lineStyle: { color: "#f59e0b", width: 2 } },
                { name: "最低", type: "line", data: tempsMin, smooth: true, symbol: "none", lineStyle: { color: "#3b82f6" } },
              ],
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>降水量</CardTitle>
        </CardHeader>
        <CardContent>
          <ReactECharts
            style={{ height: 280 }}
            notMerge
            option={{
              tooltip: { trigger: "axis" },
              grid: { top: 20, right: 24, bottom: 50, left: 50 },
              xAxis: { type: "category", data: dates, boundaryGap: false },
              yAxis: { type: "value", name: "mm" },
              dataZoom: [{ type: "inside", start: 60, end: 100 }],
              series: [{ name: "降水量", type: "bar", data: precip, itemStyle: { color: "#0ea5e9" } }],
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
