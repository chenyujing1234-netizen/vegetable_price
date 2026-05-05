"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { PriceLineChart } from "@/components/charts/PriceLineChart";
import {
  type ForecastSeries,
  type Market,
  type PriceSeries,
  type Product,
  useApi,
} from "@/lib/api";
import { formatPrice } from "@/lib/utils";

const MODELS = [
  { v: "prophet", label: "Prophet" },
  { v: "baseline", label: "Baseline" },
  { v: "lstm", label: "LSTM (规划中)" },
  { v: "ensemble", label: "集成 (规划中)" },
];

const HORIZONS = [7, 30, 90, 180, 365];

export default function PredictionsPage() {
  const { data: products } = useApi<Product[]>("/api/markets/products");
  const { data: markets } = useApi<Market[]>("/api/markets");
  const [productId, setProductId] = useState<number | null>(null);
  const [marketId, setMarketId] = useState<number | null>(null);
  const [horizon, setHorizon] = useState(30);
  const [model, setModel] = useState("prophet");

  const activeProduct = productId ?? products?.find((p) => p.code === "tomato")?.id ?? products?.[0]?.id;
  const activeMarket = marketId ?? markets?.find((m) => m.code === "shouguang")?.id ?? markets?.[0]?.id;

  const { data: history } = useApi<PriceSeries>(
    activeProduct && activeMarket
      ? `/api/prices/series?product_id=${activeProduct}&market_id=${activeMarket}&days=540`
      : null
  );
  const { data: forecast } = useApi<ForecastSeries>(
    activeProduct && activeMarket
      ? `/api/predictions/forecast?product_id=${activeProduct}&market_id=${activeMarket}&horizon_days=${horizon}&model=${model}`
      : null
  );
  const { data: metrics } = useApi<{ model: string; mae: number; mape: number; rmse: number }[]>(
    "/api/predictions/metrics"
  );

  return (
    <div>
      <PageHeader
        title="价格预测"
        description="基于 Prophet 等时序模型，输出未来价格的中位数与置信区间"
      />

      <div className="flex flex-wrap gap-3 mb-4 items-center">
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
          {HORIZONS.map((d) => (
            <Button
              key={d}
              size="sm"
              variant={horizon === d ? "default" : "outline"}
              onClick={() => setHorizon(d)}
            >
              {d} 天
            </Button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-1 mb-4">
        {MODELS.map((m) => (
          <Button
            key={m.v}
            size="sm"
            variant={model === m.v ? "default" : "outline"}
            onClick={() => setModel(m.v)}
          >
            {m.label}
          </Button>
        ))}
      </div>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>
            历史走势 + 未来 {horizon} 天预测
            {forecast && (
              <Badge variant="secondary" className="ml-2">
                model: {forecast.model}
              </Badge>
            )}
          </CardTitle>
          {forecast?.metrics && (
            <p className="text-xs text-muted-foreground">
              {Object.entries(forecast.metrics).map(([k, v]) => (
                <span key={k} className="mr-3">
                  {k}: {String(v)}
                </span>
              ))}
            </p>
          )}
        </CardHeader>
        <CardContent>
          <PriceLineChart series={history} forecast={forecast} height={420} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>未来 {horizon} 天预测明细</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[360px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="py-1">日期</th>
                    <th className="py-1">预测均价</th>
                    <th className="py-1">95% 区间</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast?.points.slice(0, 60).map((p) => (
                    <tr key={p.date} className="border-t">
                      <td className="py-1">{p.date}</td>
                      <td className="py-1 font-medium">¥{formatPrice(p.forecast)}</td>
                      <td className="py-1 text-muted-foreground">
                        ¥{formatPrice(p.lower_95)} – ¥{formatPrice(p.upper_95)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>模型评估指标</CardTitle>
            <p className="text-xs text-muted-foreground">回测 MAE / MAPE / RMSE</p>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted-foreground">
                <tr>
                  <th className="py-1">模型</th>
                  <th className="py-1">MAE</th>
                  <th className="py-1">MAPE %</th>
                  <th className="py-1">RMSE</th>
                </tr>
              </thead>
              <tbody>
                {metrics?.map((m) => (
                  <tr key={m.model} className="border-t">
                    <td className="py-1 font-medium">{m.model}</td>
                    <td className="py-1">{m.mae.toFixed(3)}</td>
                    <td className="py-1">{m.mape.toFixed(2)}</td>
                    <td className="py-1">{m.rmse.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
