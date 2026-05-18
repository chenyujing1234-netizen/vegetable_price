"use client";

import Link from "next/link";
import { Github, Gift, Sprout } from "lucide-react";

const ITEMS = [
  {
    label: "免费",
    sub: "无付费墙",
    icon: Gift,
    cls: "from-sky-500 to-sky-600 ring-sky-300/60 shadow-sky-500/20",
    dot: "bg-sky-200",
    tip: "完全免费使用，无需付费墙",
  },
  {
    label: "开源",
    sub: "代码透明",
    icon: Github,
    cls: "from-emerald-500 to-emerald-600 ring-emerald-300/60 shadow-emerald-500/20",
    dot: "bg-emerald-200",
    tip: "代码已开源在 GitHub，点击查看仓库",
    href: "https://github.com/chenyujing1234-netizen/vegetable_price",
  },
  {
    label: "助农",
    sub: "为田间地头而生",
    icon: Sprout,
    cls: "from-amber-500 to-amber-600 ring-amber-300/60 shadow-amber-500/20",
    dot: "bg-amber-200",
    tip: "点击阅读：我做这个网站的初心",
    href: "/story",
  },
] as const;

export function FeatureBadges() {
  return (
    <div className="flex flex-wrap items-stretch gap-3 mb-5">
      {ITEMS.map(({ label, sub, icon: Icon, cls, dot, tip, href }) => {
        const content = (
          <span
            className={`group relative inline-flex items-center gap-2.5 rounded-xl
                        bg-gradient-to-br ${cls}
                        px-4 py-2.5 text-white
                        ring-1 ring-inset shadow-md
                        transition-all duration-200
                        hover:-translate-y-0.5 hover:shadow-lg`}
            title={tip}
          >
            <span className="relative flex h-2 w-2">
              <span
                className={`absolute inline-flex h-full w-full animate-ping rounded-full ${dot} opacity-75`}
              />
              <span className={`relative inline-flex h-2 w-2 rounded-full ${dot}`} />
            </span>
            <Icon className="w-5 h-5" strokeWidth={2.2} aria-hidden />
            <span className="flex flex-col leading-tight">
              <span className="text-base font-bold tracking-wide">{label}</span>
              <span className="text-[10px] font-medium text-white/80">{sub}</span>
            </span>
          </span>
        );
        if (!href) {
          return (
            <span key={label} className="flex">
              {content}
            </span>
          );
        }
        const external = /^https?:\/\//.test(href);
        return external ? (
          <a
            key={label}
            href={href}
            target="_blank"
            rel="noreferrer"
            className="flex"
          >
            {content}
          </a>
        ) : (
          <Link key={label} href={href} className="flex">
            {content}
          </Link>
        );
      })}
    </div>
  );
}
