"use client";

import Image from "next/image";
import { Typewriter } from "@/components/Typewriter";

const HEADLINES = [
  "看清价格 · 预读未来 30 天走势",
  "帮你做主：这茬到底该不该种？",
  "让一年的辛苦，不再烂在田里",
];

export function HeroBanner() {
  return (
    <div className="relative overflow-hidden rounded-2xl shadow-md mb-6 ring-1 ring-black/5">
      <div className="relative aspect-[16/7] md:aspect-[16/5]">
        <Image
          src="/banner-harvest.jpg"
          alt="漳州田间，农户采摘西红柿与田头收购的真实场景"
          fill
          priority
          sizes="(max-width: 768px) 100vw, 1200px"
          className="object-cover"
        />
        <div
          className="absolute inset-0
                     bg-gradient-to-r from-black/75 via-black/40 to-transparent
                     md:from-black/70 md:via-black/25"
          aria-hidden
        />
        <div
          className="absolute inset-x-0 bottom-0 h-1/3
                     bg-gradient-to-t from-black/55 to-transparent
                     md:hidden"
          aria-hidden
        />

        <div className="absolute inset-y-0 left-0 right-0 md:right-auto
                        flex flex-col justify-center
                        px-5 md:px-10 max-w-2xl text-white">
          <p className="text-[11px] md:text-xs uppercase tracking-[0.18em]
                        text-amber-200/90 font-semibold">
            From Farm · 给田间地头的工具
          </p>

          {/* 主标题：打字机轮播 3 句话，对应网站三大目的
              加 min-h 防止文字增删时布局抖动 */}
          <h2 className="mt-2 text-xl md:text-3xl font-bold leading-snug drop-shadow
                         min-h-[2.4em] md:min-h-[1.4em]">
            <Typewriter phrases={HEADLINES} />
          </h2>

          <p className="text-sm md:text-base text-white/90 mt-3 max-w-xl leading-relaxed
                        drop-shadow-sm">
            实时呈现全国 12 个主流批发市场的蔬菜价格，预测未来走势，
            告诉农户该不该种、什么时候卖，让一年的汗水都换成实实在在的收入。
          </p>

          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-full
                             bg-white/15 backdrop-blur px-3 py-1
                             ring-1 ring-white/25">
              · 价格行情 · 30 天预测
            </span>
            <span className="inline-flex items-center gap-1 rounded-full
                             bg-white/15 backdrop-blur px-3 py-1
                             ring-1 ring-white/25">
              · 防亏增收 · 决策辅助
            </span>
            <span className="inline-flex items-center gap-1 rounded-full
                             bg-white/15 backdrop-blur px-3 py-1
                             ring-1 ring-white/25">
              · 完全免费 · 全部开源
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
