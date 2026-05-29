"use client";

import { type Product } from "@/lib/api";

export function ProductPicker({
  products,
  value,
  onChange,
  className = "",
}: {
  products: Product[];
  value: number | null | undefined;
  onChange: (id: number) => void;
  className?: string;
}) {
  return (
    <select
      className={`text-sm border rounded-md px-3 py-1.5 bg-background font-medium ${className}`}
      value={value ?? ""}
      onChange={(e) => onChange(Number(e.target.value))}
      aria-label="选择蔬菜品类"
    >
      {products.map((p) => (
        <option key={p.id} value={p.id}>
          {p.name}
          {p.spec ? `（${p.spec}）` : ""}
        </option>
      ))}
    </select>
  );
}
