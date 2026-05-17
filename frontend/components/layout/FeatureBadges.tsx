"use client";

import { Github, Gift, Sprout } from "lucide-react";

const ITEMS = [
  {
    label: "开源",
    icon: Github,
    cls: "bg-emerald-50 text-emerald-700 ring-emerald-200 hover:bg-emerald-100",
    tip: "代码已开源在 Gitee，欢迎共建",
    href: "https://gitee.com/chenyujing/vegetable",
  },
  {
    label: "免费",
    icon: Gift,
    cls: "bg-sky-50 text-sky-700 ring-sky-200 hover:bg-sky-100",
    tip: "完全免费使用，无需付费墙",
  },
  {
    label: "助农",
    icon: Sprout,
    cls: "bg-amber-50 text-amber-700 ring-amber-200 hover:bg-amber-100",
    tip: "破除信息不对称，助力田间地头",
  },
] as const;

export function FeatureBadges() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {ITEMS.map(({ label, icon: Icon, cls, tip, href }) => {
        const content = (
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1
                        text-xs font-semibold ring-1 ring-inset transition-colors ${cls}`}
            title={tip}
          >
            <Icon className="w-3.5 h-3.5" strokeWidth={2.2} />
            {label}
          </span>
        );
        return href ? (
          <a key={label} href={href} target="_blank" rel="noreferrer">
            {content}
          </a>
        ) : (
          <span key={label}>{content}</span>
        );
      })}
    </div>
  );
}
