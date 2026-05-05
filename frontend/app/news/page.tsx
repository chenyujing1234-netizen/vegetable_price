"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { type News, useApi } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

type DailySent = { date: string; avg_sentiment: number; count: number };

export default function NewsPage() {
  const { data: news } = useApi<News[]>("/api/news?product=tomato&days=180&limit=200");
  const { data: sentiment } = useApi<DailySent[]>("/api/news/sentiment-daily?product=tomato&days=180");

  return (
    <div>
      <PageHeader title="舆情新闻" description="自动抓取的西红柿/蔬菜相关新闻 + 情感打分" />

      <Card className="mb-4">
        <CardHeader>
          <CardTitle>每日情感指数</CardTitle>
          <p className="text-xs text-muted-foreground">正向 = 看涨预期；负向 = 看跌预期</p>
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
        </CardHeader>
        <CardContent className="space-y-3">
          {news?.map((n) => (
            <div key={n.id} className="border-l-2 border-primary/40 pl-3 py-1">
              <div className="flex flex-wrap items-center gap-2">
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
                    {n.sentiment_label === "positive" ? "看涨" : n.sentiment_label === "negative" ? "看跌" : "中性"}
                    {n.sentiment_score != null && ` ${n.sentiment_score.toFixed(2)}`}
                  </Badge>
                )}
                <Badge variant="outline">{n.source}</Badge>
                <span className="text-xs text-muted-foreground">
                  {new Date(n.publish_at).toLocaleString("zh-CN")}
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
              {n.keywords?.length > 0 && (
                <div className="mt-1 flex gap-1 flex-wrap">
                  {n.keywords.map((k) => (
                    <span key={k} className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                      #{k}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {!news?.length && <p className="text-sm text-muted-foreground">暂无新闻</p>}
        </CardContent>
      </Card>
    </div>
  );
}
