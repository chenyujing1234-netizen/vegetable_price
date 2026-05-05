import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(v: number | null | undefined, digits = 2) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

export function formatPct(v: number | null | undefined, digits = 1) {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(digits)}%`;
}

export function pctClass(v: number | null | undefined) {
  if (v === null || v === undefined || Number.isNaN(v)) return "text-muted-foreground";
  if (v > 0) return "text-negative font-medium";
  if (v < 0) return "text-positive font-medium";
  return "text-muted-foreground";
}
