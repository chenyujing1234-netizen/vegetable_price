import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";
import {
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  Github,
  Heart,
  LineChart,
  MessageCircle,
  TrendingUp,
} from "lucide-react";

export const metadata: Metadata = {
  title: "我们的故事 | 菜价·智算",
  description:
    "一个福建程序员，写给漳州老家亲戚的「价格地图」。让一年的辛苦，不再烂在田里。",
};

export default function StoryPage() {
  return (
    <article className="max-w-3xl mx-auto pb-16">
      {/* 返回首页 */}
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground
                   hover:text-foreground transition-colors mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        返回总览
      </Link>

      {/* Hero */}
      <header className="mb-10">
        <p className="text-xs uppercase tracking-[0.18em] text-amber-600 font-semibold">
          Our Story · 助农初心
        </p>
        <h1 className="text-3xl md:text-4xl font-bold mt-3 leading-tight tracking-tight">
          让一年的辛苦，
          <br className="md:hidden" />
          不再烂在田里
        </h1>
        <p className="text-base md:text-lg text-muted-foreground mt-3 leading-relaxed">
          一个福建程序员，写给漳州老家亲戚的"价格地图"。
        </p>
      </header>

      {/* Banner 配图（复用首页素材） */}
      <div className="relative overflow-hidden rounded-2xl shadow-md ring-1 ring-black/5 mb-10">
        <div className="relative aspect-[16/8]">
          <Image
            src="/banner-harvest.jpg"
            alt="漳州田间，农户采摘西红柿与田头收购的真实场景"
            fill
            sizes="(max-width: 768px) 100vw, 900px"
            className="object-cover"
          />
        </div>
      </div>

      {/* 正文 */}
      <div className="prose-content space-y-6 text-[15px] md:text-base leading-[1.85] text-foreground/90">
        <p>我是漳州人。</p>

        <p>
          回老家的时候，看见堂叔田里堆着没人收的红西红柿。
          他蹲在地头抽烟，一句话也不说。
          婶子在旁边小声说："今年一斤六毛，连人工都不够。再去摘，还得倒贴。"
        </p>

        <p className="font-medium">
          那一筐筐红得发亮的西红柿，被太阳晒了几天，就那么烂在了田里。
        </p>

        {/* 重点引用块 */}
        <blockquote className="border-l-4 border-amber-400 bg-amber-50/60
                                rounded-r-lg px-5 py-4 my-8
                                text-amber-900 text-[15px] leading-relaxed">
          后来我才知道，这不是堂叔一个人的事。
          <br />
          <br />
          北方寿光的西红柿大棚那年扩了 5 万亩。
          山东倒春寒少，提前一个月上市。
          那段时间销区市场刚好供过于求。
          <br />
          <br />
          这些信息，新发地、上海江桥的采购员手里都有。
          <strong>但漳州天宝镇的堂叔不知道。他只能赌一个去年的价。</strong>
        </blockquote>

        <p>
          "信息不对称"这四个字，听起来像 PPT 上的概念。
          直到我看见那块田，才知道它的真名叫"赌一年的收成"。
        </p>

        <hr className="my-10 border-dashed" />

        <h2 className="text-xl md:text-2xl font-bold mt-12 mb-4 tracking-tight">
          我用三个月，做出了这个网站
        </h2>

        <p>它做了三件事：</p>

        {/* 三件事卡片 */}
        <div className="not-prose grid gap-4 my-8">
          {[
            {
              icon: LineChart,
              cls: "bg-sky-50 text-sky-700 ring-sky-200",
              title: "把价格摆出来",
              body:
                "全国 12 个主流批发市场 —— 寿光、新发地、江桥、江南、海吉星、白沙洲……今天、昨天、一年前的价格，一目了然。这些数据本来就在那里，只是以前散落在十几个网站的角落里，没人替你拼起来。",
            },
            {
              icon: TrendingUp,
              cls: "bg-emerald-50 text-emerald-700 ring-emerald-200",
              title: "把未来 30 天预测出来",
              body:
                "基于过去 3 年的价格、本地气象、政策动态、种植面积变化，模型给出一条带置信区间的预测线。不是算命，是把那些采购员脑子里的判断，写成大家都能看的图。",
            },
            {
              icon: MessageCircle,
              cls: "bg-amber-50 text-amber-700 ring-amber-200",
              title: "把决策的依据全部摊开",
              body:
                "为什么会涨？因为寒潮来了。为什么会跌？因为收储政策结束了。模型不藏私 —— 每个因子的权重、每个判断的依据，都写在纸上。",
            },
          ].map((it, i) => (
            <div
              key={i}
              className="rounded-xl border bg-card p-5 flex gap-4 shadow-sm"
            >
              <div
                className={`shrink-0 w-10 h-10 rounded-lg flex items-center
                            justify-center ring-1 ring-inset ${it.cls}`}
              >
                <it.icon className="w-5 h-5" strokeWidth={2.2} />
              </div>
              <div>
                <h3 className="font-semibold text-base">{it.title}</h3>
                <p className="text-sm text-muted-foreground mt-1.5 leading-relaxed">
                  {it.body}
                </p>
              </div>
            </div>
          ))}
        </div>

        <hr className="my-10 border-dashed" />

        <h2 className="text-xl md:text-2xl font-bold mb-4 tracking-tight">
          它，完全免费。
        </h2>

        <p>
          农户不需要注册，不需要付钱，不需要看广告。
          代码全开源在 GitHub，谁都能 fork 去给自己家乡用。
        </p>

        <p className="text-lg font-medium">
          因为我做这个，不是为了赚谁的钱。
          <br />
          是为了让堂叔下一季种之前，能先看一眼。
          <br />
          是为了让那一筐筐红得发亮的西红柿
          <span className="text-amber-700">——不再烂在田里。</span>
        </p>
      </div>

      {/* CTA */}
      <div className="mt-16 rounded-2xl border bg-gradient-to-br from-amber-50 via-sky-50 to-emerald-50
                      p-6 md:p-8 ring-1 ring-amber-200/60">
        <div className="flex items-center gap-2 mb-4">
          <Heart className="w-5 h-5 text-amber-600" />
          <p className="font-semibold text-amber-900">
            如果你也认同这件事
          </p>
        </div>
        <p className="text-sm text-foreground/80 leading-relaxed mb-5">
          如果你身边也有种菜的亲戚，麻烦把链接发给他们。
          如果你想一起把这事做得更大，欢迎到 GitHub 提 issue —— 共建一个真正属于农户的工具。
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full
                       bg-amber-600 hover:bg-amber-700 transition-colors
                       text-white px-5 py-2.5 text-sm font-semibold shadow"
          >
            立即试用
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="https://github.com/chenyujing1234-netizen/vegetable_price"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full
                       bg-white hover:bg-gray-50 transition-colors
                       text-gray-900 px-5 py-2.5 text-sm font-semibold
                       ring-1 ring-gray-300"
          >
            <Github className="w-4 h-4" />
            GitHub 仓库
          </a>
          <a
            href="https://mp.weixin.qq.com/s/yP5xPgboCgxEF3L_DDVuIA"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-full
                       bg-white hover:bg-gray-50 transition-colors
                       text-gray-900 px-5 py-2.5 text-sm font-semibold
                       ring-1 ring-gray-300"
          >
            微信原文
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      <p className="text-xs text-muted-foreground mt-8 text-center">
        © 菜价·智算 · 一个福建漳州人的助农项目 · MIT 协议
      </p>
    </article>
  );
}
