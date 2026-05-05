"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/PageHeader";
import { type PriceHeatPoint, type Product, useApi } from "@/lib/api";
import { formatPct, formatPrice, pctClass } from "@/lib/utils";

const PriceMap = dynamic(() => import("@/components/maps/AmapPriceMap"), { ssr: false });

export default function RegionsPage() {
  const { data: products } = useApi<Product[]>("/api/markets/products");
  const [productId, setProductId] = useState<number | null>(null);
  const activeProduct = productId ?? products?.find((p) => p.code === "tomato")?.id;

  const { data: heat } = useApi<PriceHeatPoint[]>(
    activeProduct ? `/api/prices/heatmap?product_id=${activeProduct}` : null
  );

  const sorted = (heat ?? []).slice().sort((a, b) => b.avg - a.avg);
  const max = sorted[0]?.avg ?? 0;
  const min = sorted[sorted.length - 1]?.avg ?? 0;
  const spread = max && min ? ((max - min) / min) * 100 : 0;

  return (
    <div>
      <PageHeader
        title="区域分析"
        description="全国主要批发市场价格热力分布、产销价差与套利提示"
      />

      <div className="flex gap-3 mb-4">
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
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>全国市场价格分布</CardTitle>
            <p className="text-xs text-muted-foreground">
              当前数据高峰：¥{formatPrice(max)} · 低谷：¥{formatPrice(min)} · 价差 {spread.toFixed(1)}%
            </p>
          </CardHeader>
          <CardContent>
            <PriceMap points={heat ?? []} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>市场最新价格排行</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[420px] overflow-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="py-1">市场</th>
                    <th className="py-1 text-right">均价</th>
                    <th className="py-1 text-right">同比</th>
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((row) => (
                    <tr key={row.market_id} className="border-t">
                      <td className="py-1.5">{row.market_name}</td>
                      <td className="py-1.5 text-right font-medium">¥{formatPrice(row.avg)}</td>
                      <td className={`py-1.5 text-right ${pctClass(row.yoy)}`}>{formatPct(row.yoy)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
