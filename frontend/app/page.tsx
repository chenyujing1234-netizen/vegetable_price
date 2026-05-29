"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FeatureBadges } from "@/components/layout/FeatureBadges";
import { HeroBanner } from "@/components/layout/HeroBanner";
import { PageHeader } from "@/components/layout/PageHeader";
import { ProductPicker } from "@/components/layout/ProductPicker";
import { StatCard } from "@/components/layout/StatCard";
import { useSelectedProduct } from "@/lib/useSelectedProduct";
import { PriceLineChart } from "@/components/charts/PriceLineChart";
import {
  type DashboardSummary,
  type ForecastSeries,
  type Market,
  type News,
  type Policy,
  type PriceLatest,
  type PriceSeries,
  useApi,
} from "@/lib/api";
import { formatPct, formatPrice, pctClass } from "@/lib/utils";

export default function HomePage() {
  const { products, productId, product, setProductId } = useSelectedProduct();
  const { data: markets } = useApi<Market[]>("/api/markets");

  const defaultMarket = markets?.find((m) => m.code === "shouguang") ?? markets?.[0];
  const [marketId, setMarketId] = useState<number | null>(null);
  const activeMarketId = marketId ?? defaultMarket?.id ?? null;
  const productCode = product?.code ?? "tomato";

  const { data: summary } = useApi<DashboardSummary>(
    productId ? `/api/analytics/dashboard?product_id=${productId}` : null
  );
  const { data: latest } = useApi<PriceLatest[]>(
    productId ? `/api/prices/latest?product_id=${productId}` : null
  );
  const { data: series } = useApi<PriceSeries>(
    productId && activeMarketId
      ? `/api/prices/series?product_id=${productId}&market_id=${activeMarketId}&days=365`
      : null
  );
  const { data: forecast } = useApi<ForecastSeries>(
    productId && activeMarketId
      ? `/api/predictions/forecast?product_id=${productId}&market_id=${activeMarketId}&horizon_days=30`
      : null
  );
  const { data: news } = useApi<News[]>(
    productId ? `/api/news?product=${productCode}&days=60&limit=6` : null
  );
  const { data: policies } = useApi<Policy[]>(
    productId ? `/api/policies?product=${productCode}&days=720` : null
  );

  return (
    <div>
      <HeroBanner />
      <FeatureBadges />
      <PageHeader
        title={summary ? `${summary.product_name} 价格智算总览` : "价格智算总览"}
        description={
          summary
            ? `数据更新至 ${summary.as_of} · 基于 ${summary.market_coverage} 个监测市场`
            : "整合价格、天气、政策、新闻、种植面积五大维度，给出可解释的预测"
        }
        action={
          products?.length ? (
            <ProductPicker
              products={products}
              value={productId}
              onChange={setProductId}
            />
          ) : null
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="全国均价"
          value={formatPrice(summary?.national_avg_price)}
          unit="元/公斤"
          delta={summary?.mom_pct}
          hint="环比 30 天"
        />
        <StatCard
          label="同比变化"
          value={formatPct(summary?.yoy_pct)}
          delta={summary?.yoy_pct}
          hint="vs 去年同日"
        />
        <StatCard
          label={`种植面积 (${summary?.cropland_latest_year ?? "—"})`}
          value={
            summary?.cropland_total_mu
              ? `${(summary.cropland_total_mu / 10000).toFixed(1)}`
              : "—"
          }
          unit="万亩"
          delta={summary?.cropland_yoy_pct}
          hint="同比上一年"
        />
        <StatCard
          label="覆盖市场"
          value={summary?.market_coverage ?? "—"}
          unit="个"
          hint="国家级 + 地市级"
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 mb-6">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>价格走势 + 30 天预测</CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                {series ? series.market_name : "—"} · 历史 365 天 + 模型 {forecast?.model ?? "—"}
              </p>
            </div>
            <select
              className="text-sm border rounded-md px-2 py-1 bg-background"
              value={activeMarketId ?? ""}
              onChange={(e) => setMarketId(Number(e.target.value))}
            >
              {markets?.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </CardHeader>
          <CardContent>
            <PriceLineChart series={series} forecast={forecast} height={380} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>主要市场最新价格</CardTitle>
            <p className="text-xs text-muted-foreground">点击市场可切换图表</p>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[420px] overflow-auto pr-2">
            {(latest ?? []).map((row) => (
              <button
                key={row.market_id}
                onClick={() => setMarketId(row.market_id)}
                className={`w-full text-left rounded-md border px-3 py-2 hover:bg-accent transition-colors ${
                  row.market_id === activeMarketId ? "border-primary bg-primary/5" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{row.market_name}</span>
                  <span className="font-semibold">{formatPrice(row.avg)}</span>
                </div>
                <div className="flex items-center justify-between mt-1 text-xs">
                  <div className="flex gap-3">
                    <span className={pctClass(row.wow)}>周 {formatPct(row.wow)}</span>
                    <span className={pctClass(row.mom)}>月 {formatPct(row.mom)}</span>
                    <span className={pctClass(row.yoy)}>年 {formatPct(row.yoy)}</span>
                  </div>
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>近期重要政策</CardTitle>
            <p className="text-xs text-muted-foreground">影响蔬菜价格的政策动态</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {(policies ?? []).slice(0, 5).map((p) => (
              <div key={p.id} className="border-l-2 border-primary/40 pl-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant={p.impact_direction === "negative" ? "positive" : p.impact_direction === "positive" ? "negative" : "muted"}>
                    {p.impact_direction === "negative" ? "压低价格" : p.impact_direction === "positive" ? "推高价格" : "中性"}
                  </Badge>
                  <Badge variant="outline">{p.publisher}</Badge>
                  <span className="text-xs text-muted-foreground">{p.publish_date}</span>
                </div>
                <a href={p.url} className="font-medium text-sm mt-1 block hover:underline" target="_blank" rel="noreferrer">
                  {p.title}
                </a>
                {p.summary && <p className="text-xs text-muted-foreground mt-1">{p.summary}</p>}
              </div>
            ))}
            {!policies?.length && <p className="text-sm text-muted-foreground">暂无政策数据</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>舆情新闻</CardTitle>
            <p className="text-xs text-muted-foreground">已做情感打分</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {(news ?? []).map((n) => (
              <div key={n.id} className="border-l-2 border-primary/40 pl-3">
                <div className="flex items-center gap-2 flex-wrap">
                  {n.sentiment_label && (
                    <Badge
                      variant={
                        n.sentiment_label === "positive"
                          ? "negative"
                          : n.sentiment_label === "negative"
                          ? "positive"
                          : "muted"
                      }
                    >
                      {n.sentiment_label === "positive"
                        ? "看涨情绪"
                        : n.sentiment_label === "negative"
                        ? "看跌情绪"
                        : "中性"}
                    </Badge>
                  )}
                  <Badge variant="outline">{n.source}</Badge>
                  <span className="text-xs text-muted-foreground">
                    {new Date(n.publish_at).toLocaleDateString("zh-CN")}
                  </span>
                </div>
                <a
                  href={n.url}
                  className="font-medium text-sm mt-1 block hover:underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  {n.title}
                </a>
              </div>
            ))}
            {!news?.length && <p className="text-sm text-muted-foreground">暂无新闻数据</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
