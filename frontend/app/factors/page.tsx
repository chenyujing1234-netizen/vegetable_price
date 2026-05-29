"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { ProductPicker } from "@/components/layout/ProductPicker";
import { useSelectedProduct } from "@/lib/useSelectedProduct";
import {
  type CorrelationReport,
  type FactorOverview,
  type Market,
  useApi,
} from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const FEATURE_NAME: Record<string, string> = {
  temp_avg: "平均气温",
  temp_max: "最高气温",
  temp_min: "最低气温",
  precip: "降水量",
  humidity: "湿度",
};

type EventStudyRow = {
  policy_id: number;
  title: string;
  publisher: string;
  publish_date: string;
  before_avg: number;
  after_avg: number;
  abnormal_pct: number;
  impact_direction: string;
};

type GrangerResult = {
  feature?: string;
  n?: number;
  p_values?: Record<string, number>;
  error?: string;
};

export default function FactorsPage() {
  const { products, productId, product, setProductId } = useSelectedProduct();
  const { data: markets } = useApi<Market[]>("/api/markets");
  const productCode = product?.code ?? "tomato";

  const shouguang = markets?.find((m) => m.code === "shouguang");
  const [marketId, setMarketId] = useState<number | null>(null);
  const activeMarket = markets?.find((m) => m.id === (marketId ?? shouguang?.id));

  const { data: overview } = useApi<FactorOverview>(
    productId ? `/api/factors/overview?product_id=${productId}` : null
  );

  const { data: corr } = useApi<CorrelationReport>(
    productId && activeMarket
      ? `/api/factors/correlation/weather?product_id=${productId}&market_id=${activeMarket.id}&region_code=${activeMarket.region_code}&days=720`
      : null
  );

  const { data: events } = useApi<EventStudyRow[]>(
    productId && activeMarket
      ? `/api/factors/event-study/policy?product_id=${productId}&market_id=${activeMarket.id}&product_code=${productCode}&window=30`
      : null
  );

  const { data: granger } = useApi<GrangerResult>(
    productId && activeMarket
      ? `/api/factors/granger/weather?product_id=${productId}&market_id=${activeMarket.id}&region_code=${activeMarket.region_code}&feature=temp_avg&max_lag=7`
      : null
  );

  return (
    <div>
      <PageHeader
        title="影响因子分析"
        description="基于学术研究的影响因子框架 + 实时数据相关性、格兰杰因果与事件研究"
        action={
          products?.length ? (
            <ProductPicker products={products} value={productId} onChange={setProductId} />
          ) : null
        }
      />

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>{overview?.product_name ?? "西红柿"} 价格影响因子全景</CardTitle>
          <p className="text-xs text-muted-foreground">
            参考 PLOS One、华南农业大学等论文综合得到的因子权重
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {overview?.factors.map((f) => (
              <div key={f.factor} className="border rounded-md p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{f.name}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{f.description}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge
                      variant={
                        f.direction === "positive"
                          ? "negative"
                          : f.direction === "negative"
                          ? "positive"
                          : "muted"
                      }
                    >
                      {f.direction === "positive" ? "正向" : f.direction === "negative" ? "反向" : "双向"}
                    </Badge>
                    <span className="text-sm font-semibold">权重 {(f.weight * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary"
                    style={{ width: `${Math.min(100, f.weight * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>价格 ⇄ 天气 相关性</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                产区市场近 720 天皮尔逊相关系数
              </p>
            </div>
            <select
              className="text-sm border rounded-md px-2 py-1 bg-background"
              value={activeMarket?.id ?? ""}
              onChange={(e) => setMarketId(Number(e.target.value))}
            >
              {markets?.filter((m) => m.is_origin).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </CardHeader>
          <CardContent>
            {corr && corr.items.length > 0 ? (
              <ReactECharts
                style={{ height: 320 }}
                notMerge
                option={{
                  grid: { top: 30, left: 90, right: 30, bottom: 30 },
                  xAxis: { type: "value", min: -1, max: 1 },
                  yAxis: {
                    type: "category",
                    data: corr.items.map((i) => FEATURE_NAME[i.feature] ?? i.feature),
                  },
                  series: [
                    {
                      type: "bar",
                      data: corr.items.map((i) => ({
                        value: i.correlation,
                        itemStyle: { color: i.correlation > 0 ? "#ef4444" : "#16a34a" },
                      })),
                      label: {
                        show: true,
                        position: "right",
                        formatter: (p: any) => p.value.toFixed(2),
                      },
                    },
                  ],
                  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
                }}
              />
            ) : (
              <p className="text-sm text-muted-foreground">暂无相关性数据</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>格兰杰因果检验：气温 → 价格</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              p &lt; 0.05 表示在该 lag 上气温显著影响价格
            </p>
          </CardHeader>
          <CardContent>
            {granger?.error ? (
              <p className="text-sm text-muted-foreground">{granger.error}</p>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted-foreground">
                  <tr>
                    <th className="py-1">滞后阶数</th>
                    <th className="py-1">p-value</th>
                    <th className="py-1">显著性</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(granger?.p_values ?? {}).map(([k, v]) => (
                    <tr key={k} className="border-t">
                      <td className="py-1">{k}</td>
                      <td className="py-1 font-mono">{v.toFixed(4)}</td>
                      <td className="py-1">
                        {v < 0.01 ? (
                          <Badge variant="negative">***</Badge>
                        ) : v < 0.05 ? (
                          <Badge variant="negative">**</Badge>
                        ) : v < 0.1 ? (
                          <Badge variant="muted">*</Badge>
                        ) : (
                          <span className="text-muted-foreground text-xs">不显著</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>政策事件研究</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">
            每条政策发布日前后 30 天的价格平均偏离（abnormal return）
          </p>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead className="text-left text-xs text-muted-foreground">
              <tr>
                <th className="py-1">发布日</th>
                <th className="py-1">政策</th>
                <th className="py-1 text-right">前 30 天均价</th>
                <th className="py-1 text-right">后 30 天均价</th>
                <th className="py-1 text-right">异常涨跌</th>
              </tr>
            </thead>
            <tbody>
              {events?.map((e) => (
                <tr key={e.policy_id} className="border-t">
                  <td className="py-2 whitespace-nowrap">{e.publish_date}</td>
                  <td className="py-2">
                    <div className="font-medium">{e.title}</div>
                    <div className="text-xs text-muted-foreground">{e.publisher}</div>
                  </td>
                  <td className="py-2 text-right">¥{e.before_avg.toFixed(2)}</td>
                  <td className="py-2 text-right">¥{e.after_avg.toFixed(2)}</td>
                  <td
                    className={`py-2 text-right font-medium ${
                      e.abnormal_pct > 0 ? "text-negative" : e.abnormal_pct < 0 ? "text-positive" : ""
                    }`}
                  >
                    {e.abnormal_pct > 0 ? "+" : ""}
                    {e.abnormal_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
              {!events?.length && (
                <tr>
                  <td colSpan={5} className="py-3 text-sm text-muted-foreground text-center">
                    暂无政策事件数据
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
