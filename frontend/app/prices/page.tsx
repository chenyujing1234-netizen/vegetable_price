"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/PageHeader";
import { PriceLineChart } from "@/components/charts/PriceLineChart";
import { type Market, type PriceSeries, type Product, useApi } from "@/lib/api";
import { formatPrice } from "@/lib/utils";

const RANGES = [
  { label: "30 天", days: 30 },
  { label: "90 天", days: 90 },
  { label: "365 天", days: 365 },
  { label: "近 3 年", days: 1095 },
];

export default function PricesPage() {
  const { data: products } = useApi<Product[]>("/api/markets/products");
  const { data: markets } = useApi<Market[]>("/api/markets");
  const [productId, setProductId] = useState<number | null>(null);
  const [marketId, setMarketId] = useState<number | null>(null);
  const [days, setDays] = useState(365);

  const activeProduct = productId ?? products?.[0]?.id;
  const activeMarket = marketId ?? markets?.find((m) => m.code === "shouguang")?.id ?? markets?.[0]?.id;

  const { data: series } = useApi<PriceSeries>(
    activeProduct && activeMarket
      ? `/api/prices/series?product_id=${activeProduct}&market_id=${activeMarket}&days=${days}`
      : null
  );

  const stats = series ? computeStats(series) : null;

  return (
    <div>
      <PageHeader title="价格行情" description="查看各市场各品类历史价格走势与统计指标" />

      <div className="flex flex-wrap gap-3 mb-4">
        <select
          className="text-sm border rounded-md px-3 py-1.5 bg-background"
          value={activeProduct ?? ""}
          onChange={(e) => setProductId(Number(e.target.value))}
        >
          {products?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <select
          className="text-sm border rounded-md px-3 py-1.5 bg-background"
          value={activeMarket ?? ""}
          onChange={(e) => setMarketId(Number(e.target.value))}
        >
          {markets?.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
        <div className="ml-auto flex gap-1">
          {RANGES.map((r) => (
            <Button
              key={r.days}
              size="sm"
              variant={days === r.days ? "default" : "outline"}
              onClick={() => setDays(r.days)}
            >
              {r.label}
            </Button>
          ))}
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <Stat label="均价" value={`¥${formatPrice(stats.mean)}`} />
          <Stat label="最高价" value={`¥${formatPrice(stats.max)}`} sub={stats.maxDate} />
          <Stat label="最低价" value={`¥${formatPrice(stats.min)}`} sub={stats.minDate} />
          <Stat label="波动率" value={`${(stats.cv * 100).toFixed(1)}%`} sub="变异系数 CV" />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{series?.market_name ?? ""} · {series?.product_name ?? ""} 价格曲线</CardTitle>
        </CardHeader>
        <CardContent>
          <PriceLineChart series={series} height={460} />
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-xl font-semibold mt-1">{value}</div>
        {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
      </CardContent>
    </Card>
  );
}

function computeStats(s: PriceSeries) {
  const arr = s.points.map((p) => p.avg);
  if (!arr.length) return null;
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
  const max = Math.max(...arr);
  const min = Math.min(...arr);
  const maxIdx = arr.indexOf(max);
  const minIdx = arr.indexOf(min);
  const variance = arr.reduce((a, b) => a + (b - mean) ** 2, 0) / arr.length;
  const std = Math.sqrt(variance);
  return {
    mean,
    max,
    min,
    maxDate: s.points[maxIdx].date,
    minDate: s.points[minIdx].date,
    cv: mean > 0 ? std / mean : 0,
  };
}
