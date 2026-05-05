import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "菜价·智算 | 蔬菜价格预测 SaaS",
  description: "面向农户、采购商和政策研究者的蔬菜价格预测平台",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen flex">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="container mx-auto py-6 px-4 md:px-6">{children}</div>
        </main>
      </body>
    </html>
  );
}
