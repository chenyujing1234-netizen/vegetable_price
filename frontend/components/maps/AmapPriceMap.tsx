"use client";

/**
 * 高德地图（AMap）版本的价格热力 + 标点。
 *
 * 使用前提：在 `.env.local` 中设置 `NEXT_PUBLIC_AMAP_KEY` 和（推荐）
 * `NEXT_PUBLIC_AMAP_SECURITY_CODE`。如未设置 KEY 会优雅地降级到
 * ECharts 散点版本（`PriceMap.tsx`）。
 *
 * 高德 JS API 通过运行时动态注入 script，无需 npm 包；可避免 next 服务端
 * 渲染时报 window not defined。
 */

import { useEffect, useRef } from "react";
import type { PriceHeatPoint } from "@/lib/api";
import PriceMap from "./PriceMap";

declare global {
  interface Window {
    AMap?: any;
    _AMapSecurityConfig?: { securityJsCode: string };
  }
}

const AMAP_VERSION = "2.0";
const AMAP_PLUGINS = ["AMap.HeatMap", "AMap.MarkerCluster", "AMap.MoveAnimation"];

function loadAMap(key: string, securityCode?: string): Promise<any> {
  if (typeof window === "undefined") return Promise.reject("ssr");
  if (window.AMap) return Promise.resolve(window.AMap);
  if (securityCode) {
    window._AMapSecurityConfig = { securityJsCode: securityCode };
  }
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${key}&plugin=${AMAP_PLUGINS.join(",")}`;
    script.async = true;
    script.onload = () => resolve(window.AMap);
    script.onerror = (e) => reject(e);
    document.head.appendChild(script);
  });
}

export default function AmapPriceMap({ points }: { points: PriceHeatPoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const key = process.env.NEXT_PUBLIC_AMAP_KEY;
  const sc = process.env.NEXT_PUBLIC_AMAP_SECURITY_CODE;

  useEffect(() => {
    if (!key || !containerRef.current) return;
    let disposed = false;

    loadAMap(key, sc).then((AMap) => {
      if (disposed || !containerRef.current) return;
      const map = new AMap.Map(containerRef.current, {
        zoom: 4.5,
        center: [104.0, 35.0],
        viewMode: "2D",
        mapStyle: "amap://styles/whitesmallow",
      });
      mapRef.current = map;

      const data = points
        .filter((p) => p.lng != null && p.lat != null)
        .map((p) => ({
          lng: p.lng as number,
          lat: p.lat as number,
          count: p.avg,
          name: p.market_name,
          yoy: p.yoy,
        }));

      const heat = new AMap.HeatMap(map, {
        radius: 40,
        opacity: [0, 0.85],
        gradient: { 0.3: "#16a34a", 0.5: "#fbbf24", 0.7: "#f97316", 0.9: "#dc2626" },
      });
      heat.setDataSet({
        data,
        max: Math.max(...data.map((d) => d.count), 6),
      });

      data.forEach((d) => {
        const marker = new AMap.Marker({
          position: [d.lng, d.lat],
          title: d.name,
          anchor: "center",
          offset: new AMap.Pixel(0, 0),
          content: `
            <div style="background:#fff;border:1px solid #16a34a;border-radius:6px;padding:4px 8px;
              font-size:12px;color:#0f172a;box-shadow:0 1px 4px rgba(0,0,0,0.1);white-space:nowrap;">
              ${d.name} <strong style="color:#16a34a">¥${d.count.toFixed(2)}</strong>
            </div>
          `,
        });
        marker.setMap(map);
      });
    });

    return () => {
      disposed = true;
      mapRef.current?.destroy?.();
    };
  }, [key, sc, points]);

  if (!key) {
    return (
      <div>
        <div className="text-xs text-muted-foreground mb-2">
          未配置 NEXT_PUBLIC_AMAP_KEY，已降级为 ECharts 散点视图。
        </div>
        <PriceMap points={points} />
      </div>
    );
  }

  return <div ref={containerRef} className="w-full" style={{ height: 520, borderRadius: 8 }} />;
}
