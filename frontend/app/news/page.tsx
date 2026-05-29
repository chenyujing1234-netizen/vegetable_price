"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/layout/PageHeader";
import { ProductPicker } from "@/components/layout/ProductPicker";
import {
  type News,
  type NewsAnalyzeResult,
  analyzeNews,
  useApi,
} from "@/lib/api";
import { useSelectedProduct } from "@/lib/useSelectedProduct";
import { Loader2, Sparkles } from "lucide-react";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

type DailySent = { date: string; avg_sentiment: number; count: number };
type SourceStat = { source: string; count: number };

const IMPACT_LABEL: Record<string, string> = {
  likely_up: "偏多 · 价格可能走强",
  likely_down: "偏空 · 价格可能承压",
  neutral: "中性 · 方向不明",
};

export default function NewsPage() {
  const { products, productId, product, setProductId } = useSelectedProduct();
  const productCode = product?.code ?? "tomato";
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);
  const [analysisMap, setAnalysisMap] = useState<Record<number, NewsAnalyzeResult>>({});
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const newsUrl = productId
    ? `/api/news?product=${productCode}&days=730&limit=200${
        sourceFilter ? `&source=${encodeURIComponent(sourceFilter)}` : ""
      }`
    : null;

  const { data: news, mutate: mutateNews } = useApi<News[]>(newsUrl);
  const { data: sentiment } = useApi<DailySent[]>(
    productId ? `/api/news/sentiment-daily?product=${productCode}&days=730` : null
  );
  const { data: sources } = useApi<SourceStat[]>("/api/news/sources");

  const handleAnalyze = async (item: News) => {
    if (analysisMap[item.id]?.analysis_status === "done") {
      setExpandedId(expandedId === item.id ? null : item.id);
      return;
    }
    setAnalyzingId(item.id);
    setError(null);
    try {
      const result = await analyzeNews(item.id);
      setAnalysisMap((m) => ({ ...m, [item.id]: result }));
      setExpandedId(item.id);
      await mutateNews();
    } catch (e) {
      setError(e instanceof Error ? e.message : "解读失败");
    } finally {
      setAnalyzingId(null);
    }
  };

  return (
    <div>
      <PageHeader
        title="舆情新闻"
        description={
          product
            ? `${product.name} 相关新闻 · 来自农民日报、中国农业新闻网等固定来源 · 点击「解读」按需分析`
            : "固定来源农业新闻 · 点击「解读」生成平台观点"
        }
        action={
          products?.length ? (
            <ProductPicker products={products} value={productId} onChange={setProductId} />
          ) : null
        }
      />

      {/* 固定来源筛选 */}
      <div className="flex flex-wrap gap-2 mb-4">
        <Button
          size="sm"
          variant={sourceFilter === "" ? "default" : "outline"}
          onClick={() => setSourceFilter("")}
        >
          全部来源
        </Button>
        {sources?.slice(0, 8).map((s) => (
          <Button
            key={s.source}
            size="sm"
            variant={sourceFilter === s.source ? "default" : "outline"}
            onClick={() => setSourceFilter(s.source)}
          >
            {s.source}
            <span className="ml-1 opacity-70">({s.count})</span>
          </Button>
        ))}
      </div>

      {error && (
        <p className="text-sm text-red-600 mb-4 bg-red-50 border border-red-200 rounded-md px-3 py-2">
          {error}
        </p>
      )}

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>每日情感指数</CardTitle>
          <p className="text-xs text-muted-foreground">
            基于标题/quick 情感；点击单篇「解读」可抓取正文并生成详细观点
          </p>
        </CardHeader>
        <CardContent>
          <ReactECharts
            style={{ height: 280 }}
            notMerge
            option={{
              tooltip: { trigger: "axis" },
              grid: { top: 20, right: 24, bottom: 50, left: 50 },
              xAxis: { type: "category", data: sentiment?.map((s) => s.date) ?? [] },
              yAxis: { type: "value", name: "情感分", min: -1, max: 1 },
              series: [
                {
                  type: "bar",
                  data: sentiment?.map((s) => ({
                    value: s.avg_sentiment,
                    itemStyle: { color: s.avg_sentiment >= 0 ? "#ef4444" : "#16a34a" },
                  })) ?? [],
                  barMaxWidth: 14,
                },
              ],
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>近期新闻列表</CardTitle>
          <p className="text-xs text-muted-foreground">
            不预跑全文分析；点击「解读本篇」后才会抓取正文并给出平台观点
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {news?.map((n) => {
            const cached = analysisMap[n.id];
            const detail = cached?.analysis_detail;
            const isExpanded = expandedId === n.id;
            const isLoading = analyzingId === n.id;

            return (
              <div key={n.id} className="border rounded-lg p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
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
                            ? "看涨"
                            : n.sentiment_label === "negative"
                            ? "看跌"
                            : "中性"}
                        </Badge>
                      )}
                      <Badge variant="outline">{n.source}</Badge>
                      {n.has_analysis && (
                        <Badge variant="secondary" className="bg-emerald-50 text-emerald-700">
                          已解读
                        </Badge>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {new Date(n.publish_at).toLocaleString("zh-CN")}
                      </span>
                    </div>
                    <a
                      href={n.url}
                      className="font-medium text-sm hover:underline block"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {n.title}
                    </a>
                  </div>
                  <Button
                    size="sm"
                    variant={isExpanded ? "secondary" : "default"}
                    disabled={isLoading}
                    onClick={() => handleAnalyze(n)}
                    className="shrink-0"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                        解读中…
                      </>
                    ) : isExpanded || n.has_analysis ? (
                      <>
                        <Sparkles className="w-4 h-4 mr-1" />
                        {isExpanded ? "收起解读" : "查看解读"}
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-1" />
                        解读本篇
                      </>
                    )}
                  </Button>
                </div>

                {isExpanded && (cached || n.analysis_summary) && (
                  <div className="mt-4 rounded-md bg-amber-50/80 border border-amber-200/60 p-4 text-sm space-y-3">
                    <p className="font-semibold text-amber-900 flex items-center gap-1">
                      <Sparkles className="w-4 h-4" />
                      平台解读观点
                    </p>
                    <p className="text-foreground/90 leading-relaxed">
                      {cached?.analysis_summary ?? n.analysis_summary}
                    </p>
                    {detail && (
                      <>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">
                            {IMPACT_LABEL[detail.price_impact] ?? detail.price_impact}
                          </Badge>
                          {detail.mentioned_products_cn?.map((p) => (
                            <Badge key={p} variant="secondary">
                              {p}
                            </Badge>
                          ))}
                        </div>
                        {detail.key_factors?.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">
                              识别因子
                            </p>
                            <ul className="list-disc pl-5 space-y-0.5 text-foreground/80">
                              {detail.key_factors.map((f) => (
                                <li key={f.id}>
                                  {f.name}：{f.evidence}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <p className="text-foreground/90">
                          <span className="font-medium">给农户的建议：</span>
                          {detail.farmer_advice}
                        </p>
                        <p className="text-xs text-muted-foreground">{detail.disclaimer}</p>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          })}
          {!news?.length && (
            <p className="text-sm text-muted-foreground">
              暂无新闻。可运行爬虫抓取固定来源：
              <code className="text-xs bg-muted px-1 rounded ml-1">
                python -m news.aggregator --sources farmer,agri
              </code>
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
