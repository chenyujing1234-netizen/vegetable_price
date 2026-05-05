import useSWR from "swr";

// 默认走相对路径，由 Next.js rewrite 代理到后端，避免 CORS 与跨主机访问问题。
// 仅在显式配置 NEXT_PUBLIC_API_BASE 时才直连后端。
const BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export const fetcher = async (url: string) => {
  const res = await fetch(url.startsWith("http") ? url : `${BASE}${url}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
};

export function useApi<T>(path: string | null) {
  return useSWR<T>(path, fetcher, {
    revalidateOnFocus: false,
    keepPreviousData: true,
  });
}

export type Market = {
  id: number;
  code: string;
  name: string;
  region_code: string;
  level: string;
  is_origin: boolean;
  is_destination: boolean;
  lng: number | null;
  lat: number | null;
};

export type Product = {
  id: number;
  code: string;
  name: string;
  category: string;
  spec: string | null;
  unit: string;
};

export type PricePoint = {
  date: string;
  avg: number;
  low: number | null;
  high: number | null;
  volume: number | null;
};

export type PriceSeries = {
  market_id: number;
  market_name: string;
  product_id: number;
  product_name: string;
  points: PricePoint[];
};

export type PriceLatest = {
  market_id: number;
  market_name: string;
  product_id: number;
  product_name: string;
  date: string;
  avg: number;
  yoy: number | null;
  mom: number | null;
  wow: number | null;
};

export type PriceHeatPoint = {
  market_id: number;
  market_name: string;
  region_code: string;
  lng: number | null;
  lat: number | null;
  avg: number;
  yoy: number | null;
};

export type ForecastPoint = {
  date: string;
  forecast: number;
  lower_80: number | null;
  upper_80: number | null;
  lower_95: number | null;
  upper_95: number | null;
};

export type ForecastSeries = {
  market_id: number;
  market_name: string;
  product_id: number;
  product_name: string;
  model: string;
  run_at: string;
  horizon_days: number;
  points: ForecastPoint[];
  metrics: Record<string, unknown> | null;
};

export type WeatherSeries = {
  region_code: string;
  region_name: string;
  points: {
    date: string;
    temp_min: number | null;
    temp_max: number | null;
    temp_avg: number | null;
    precip: number | null;
    humidity: number | null;
    wind_speed: number | null;
    weather: string | null;
  }[];
};

export type News = {
  id: number;
  title: string;
  source: string;
  url: string;
  publish_at: string;
  sentiment_score: number | null;
  sentiment_label: string | null;
  keywords: string[];
};

export type Policy = {
  id: number;
  title: string;
  publisher: string;
  publish_date: string;
  url: string;
  summary: string | null;
  impact_level: string;
  impact_direction: string;
  related_products: string[];
  keywords: string[];
};

export type FactorScore = {
  factor: string;
  name: string;
  weight: number;
  direction: string;
  description: string;
};

export type FactorOverview = {
  product_id: number;
  product_name: string;
  factors: FactorScore[];
};

export type CorrelationItem = {
  feature: string;
  correlation: number;
  p_value: number | null;
};

export type CorrelationReport = {
  target: string;
  items: CorrelationItem[];
};

export type DashboardSummary = {
  product_id: number;
  product_name: string;
  as_of: string;
  national_avg_price: number | null;
  yoy_pct: number | null;
  mom_pct: number | null;
  market_coverage: number;
  cropland_latest_year: number | null;
  cropland_total_mu: number | null;
  cropland_yoy_pct: number | null;
};
