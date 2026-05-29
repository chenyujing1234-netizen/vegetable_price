"use client";

import { useEffect, useState } from "react";
import { type Product, useApi } from "@/lib/api";

const STORAGE_KEY = "veg-selected-product-id";

/** 全站共享的当前选中品类，写入 localStorage，切换页面后仍保留。 */
export function useSelectedProduct(defaultCode = "tomato") {
  const { data: products } = useApi<Product[]>("/api/markets/products");
  const [productId, setProductIdState] = useState<number | null>(null);

  useEffect(() => {
    if (!products?.length) return;

    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const id = Number(stored);
      if (products.some((p) => p.id === id)) {
        setProductIdState(id);
        return;
      }
    }

    const fallback =
      products.find((p) => p.code === defaultCode)?.id ?? products[0]?.id ?? null;
    setProductIdState(fallback);
  }, [products, defaultCode]);

  const setProductId = (id: number) => {
    setProductIdState(id);
    localStorage.setItem(STORAGE_KEY, String(id));
  };

  const product = products?.find((p) => p.id === productId) ?? null;

  return { products, productId, product, setProductId };
}
