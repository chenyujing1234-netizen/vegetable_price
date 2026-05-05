"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  TrendingUp,
  Cloud,
  FileText,
  Newspaper,
  Map as MapIcon,
  Sprout,
  Bell,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "总览", icon: Home },
  { href: "/prices", label: "价格行情", icon: TrendingUp },
  { href: "/predictions", label: "价格预测", icon: Sprout },
  { href: "/factors", label: "影响因子", icon: FileText },
  { href: "/regions", label: "区域分析", icon: MapIcon },
  { href: "/weather", label: "天气数据", icon: Cloud },
  { href: "/news", label: "舆情新闻", icon: Newspaper },
  { href: "/alerts", label: "价格告警", icon: Bell },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 shrink-0 border-r bg-card/50 px-3 py-4 hidden md:flex md:flex-col">
      <div className="px-3 pb-4 mb-2 border-b">
        <div className="font-bold text-lg flex items-center gap-2">
          <span className="text-primary">菜价</span>
          <span>·智算</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">Vegetable Price Intelligence</p>
      </div>
      <nav className="space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-3 pt-3 border-t text-xs text-muted-foreground">
        <p>v0.1.0 · MVP</p>
      </div>
    </aside>
  );
}
