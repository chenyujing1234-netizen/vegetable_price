import Image from "next/image";

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
                        px-5 md:px-10 max-w-xl text-white">
          <p className="text-[11px] md:text-xs uppercase tracking-[0.18em]
                        text-amber-200/90 font-semibold">
            From Farm · 给田间地头的工具
          </p>
          <h2 className="text-xl md:text-3xl font-bold mt-2 leading-snug drop-shadow">
            让每一筐西红柿，
            <br />
            都在最值钱的时刻被收购
          </h2>
          <p className="text-sm md:text-base text-white/90 mt-3 max-w-md leading-relaxed
                        drop-shadow-sm">
            整合 12 个批发市场实时价格、本地气象、政策动态与种植面积数据，
            给农户一个"该不该种、什么时候卖"的清楚答案。
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-full
                             bg-white/15 backdrop-blur px-3 py-1
                             ring-1 ring-white/25">
              · 实时价格 · 30 天预测
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
