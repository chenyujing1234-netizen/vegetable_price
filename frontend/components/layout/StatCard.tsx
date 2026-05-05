import { Card, CardContent } from "@/components/ui/card";
import { ArrowDown, ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  unit,
  delta,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  unit?: string;
  delta?: number | null;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
        <div className="flex items-baseline gap-2 mt-2">
          <span className="text-2xl font-bold">{value}</span>
          {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
        </div>
        <div className="flex items-center justify-between mt-2 text-xs">
          {delta !== undefined && delta !== null ? (
            <div
              className={cn(
                "flex items-center gap-0.5",
                delta > 0 ? "text-negative" : delta < 0 ? "text-positive" : "text-muted-foreground"
              )}
            >
              {delta > 0 ? <ArrowUp className="h-3 w-3" /> : delta < 0 ? <ArrowDown className="h-3 w-3" /> : null}
              <span>{delta.toFixed(1)}%</span>
            </div>
          ) : (
            <span />
          )}
          {hint && <span className="text-muted-foreground">{hint}</span>}
        </div>
      </CardContent>
    </Card>
  );
}
