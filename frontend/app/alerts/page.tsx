"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/layout/PageHeader";
import { Bell, LogOut } from "lucide-react";
import { type Market, type Product, useApi } from "@/lib/api";
import { authedFetch, clearSession, setSession, useAuth } from "@/lib/auth";

const RULES: { v: string; label: string; unit: string }[] = [
  { v: "below", label: "价格低于", unit: "元/公斤" },
  { v: "above", label: "价格高于", unit: "元/公斤" },
  { v: "yoy_above", label: "同比涨幅大于", unit: "%" },
  { v: "mom_above", label: "环比涨幅大于", unit: "%" },
];

type Alert = {
  id: number;
  market_id: number | null;
  product_id: number;
  rule: string;
  threshold: number;
  channel: string;
  webhook_url: string | null;
  is_active: boolean;
  last_triggered_at: string | null;
  created_at: string;
};

export default function AlertsPage() {
  const user = useAuth();
  return (
    <div>
      <PageHeader
        title="价格告警"
        description="设置价格阈值，达到时通过邮件 / Webhook 推送通知（Free 版每用户最多 3 条）"
        action={
          user && (
            <Button variant="outline" onClick={clearSession}>
              <LogOut className="h-4 w-4 mr-1" />
              退出登录
            </Button>
          )
        }
      />
      {user ? <AlertsBoard /> : <AuthCard />}
    </div>
  );
}

function AuthCard() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setError(null);
    setLoading(true);
    try {
      const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body = mode === "login"
        ? { email, password }
        : { email, name, password };
      const res = await authedFetch(path, { method: "POST", body: JSON.stringify(body) });
      setSession(res.access_token, {
        user_id: res.user_id, email: res.email, name: res.name, plan: res.plan,
      });
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>{mode === "login" ? "登录" : "注册"}</CardTitle>
          <p className="text-xs text-muted-foreground">仅用于价格告警订阅，不会向第三方共享</p>
        </CardHeader>
        <CardContent className="space-y-3">
          <input
            className="w-full border rounded-md px-3 py-2 text-sm"
            placeholder="邮箱"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          {mode === "register" && (
            <input
              className="w-full border rounded-md px-3 py-2 text-sm"
              placeholder="姓名"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          )}
          <input
            className="w-full border rounded-md px-3 py-2 text-sm"
            placeholder="密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <Button onClick={submit} disabled={loading} className="w-full">
            {loading ? "提交中…" : mode === "login" ? "登录" : "注册并登录"}
          </Button>
          <button
            className="text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "没有账号？立即注册" : "已有账号？登录"}
          </button>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertsBoard() {
  const { data: products } = useApi<Product[]>("/api/markets/products");
  const { data: markets } = useApi<Market[]>("/api/markets");
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [showNew, setShowNew] = useState(false);

  async function refresh() {
    try {
      setAlerts(await authedFetch("/api/alerts"));
    } catch {
      setAlerts([]);
    }
  }

  useEffect(() => { refresh(); }, []);

  const productMap = Object.fromEntries((products ?? []).map((p) => [p.id, p.name]));
  const marketMap = Object.fromEntries((markets ?? []).map((m) => [m.id, m.name]));

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={() => setShowNew(true)}>
          <Bell className="h-4 w-4 mr-1" /> 新建告警
        </Button>
      </div>

      {showNew && (
        <NewAlertForm
          products={products ?? []}
          markets={markets ?? []}
          onClose={() => setShowNew(false)}
          onSaved={() => { setShowNew(false); refresh(); }}
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>我的告警规则</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border divide-y">
            {(alerts ?? []).map((r) => (
              <div key={r.id} className="flex items-center justify-between p-3">
                <div>
                  <div className="font-medium text-sm">
                    {productMap[r.product_id] ?? `#${r.product_id}`} ·{" "}
                    {r.market_id ? marketMap[r.market_id] : "全国均价"}{" "}
                    {RULES.find((x) => x.v === r.rule)?.label} {r.threshold}
                    {r.rule.includes("above") && r.rule !== "above" ? "%" : ""}
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    通道：{r.channel} · 创建于 {new Date(r.created_at).toLocaleDateString("zh-CN")}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={r.is_active ? "positive" : "muted"}>
                    {r.is_active ? "启用" : "暂停"}
                  </Badge>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={async () => {
                      await authedFetch(`/api/alerts/${r.id}`, { method: "DELETE" });
                      refresh();
                    }}
                  >
                    删除
                  </Button>
                </div>
              </div>
            ))}
            {alerts && alerts.length === 0 && (
              <div className="p-6 text-sm text-muted-foreground text-center">
                还没有告警规则，点击右上角新建。
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function NewAlertForm({
  products, markets, onClose, onSaved,
}: { products: Product[]; markets: Market[]; onClose: () => void; onSaved: () => void; }) {
  const [productId, setProductId] = useState<number>(products[0]?.id ?? 0);
  const [marketId, setMarketId] = useState<number | null>(null);
  const [rule, setRule] = useState("below");
  const [threshold, setThreshold] = useState<number>(3);
  const [channel, setChannel] = useState("email");
  const [webhook, setWebhook] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    try {
      await authedFetch("/api/alerts", {
        method: "POST",
        body: JSON.stringify({
          product_id: productId,
          market_id: marketId,
          rule,
          threshold,
          channel,
          webhook_url: channel.includes("webhook") ? webhook : null,
        }),
      });
      onSaved();
    } catch (e: any) {
      setErr(e.message);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle>新建告警</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClose}>取消</Button>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Field label="产品">
          <select className="w-full border rounded-md px-3 py-2 text-sm" value={productId} onChange={(e) => setProductId(Number(e.target.value))}>
            {products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </Field>
        <Field label="市场（留空 = 全国均价）">
          <select className="w-full border rounded-md px-3 py-2 text-sm" value={marketId ?? ""} onChange={(e) => setMarketId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">全国均价</option>
            {markets.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </Field>
        <Field label="规则">
          <select className="w-full border rounded-md px-3 py-2 text-sm" value={rule} onChange={(e) => setRule(e.target.value)}>
            {RULES.map((r) => <option key={r.v} value={r.v}>{r.label}</option>)}
          </select>
        </Field>
        <Field label={`阈值 (${RULES.find((r) => r.v === rule)?.unit})`}>
          <input type="number" step="0.1" className="w-full border rounded-md px-3 py-2 text-sm" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} />
        </Field>
        <Field label="通知通道">
          <select className="w-full border rounded-md px-3 py-2 text-sm" value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="email">邮件</option>
            <option value="email,webhook">邮件 + Webhook</option>
            <option value="webhook">仅 Webhook</option>
          </select>
        </Field>
        {channel.includes("webhook") && (
          <Field label="Webhook URL">
            <input className="w-full border rounded-md px-3 py-2 text-sm" placeholder="https://..." value={webhook} onChange={(e) => setWebhook(e.target.value)} />
          </Field>
        )}
        <div className="md:col-span-2 flex items-center gap-3">
          <Button onClick={save}>保存</Button>
          {err && <span className="text-sm text-destructive">{err}</span>}
        </div>
      </CardContent>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}
