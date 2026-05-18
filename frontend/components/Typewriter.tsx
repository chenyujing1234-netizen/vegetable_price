"use client";

import { useEffect, useState } from "react";

interface TypewriterProps {
  phrases: string[];
  typeSpeed?: number;
  deleteSpeed?: number;
  pauseTime?: number;
  loop?: boolean;
  className?: string;
  cursorClassName?: string;
}

/**
 * 打字机效果：逐字写出 phrases 中的每一句，写完停顿后逐字删除并切换下一句。
 *
 * 设计要点：
 * - 用 setTimeout 链式驱动，避免 setInterval 在 phase 切换时累计漂移
 * - 光标用 `▍`（半角实心竖条）+ animate-pulse，比 `|` 更醒目
 * - 默认 loop=true，会无限循环
 */
export function Typewriter({
  phrases,
  typeSpeed = 95,
  deleteSpeed = 45,
  pauseTime = 2200,
  loop = true,
  className,
  cursorClassName = "ml-0.5 inline-block w-[0.08em] -translate-y-[2px] text-amber-300/90",
}: TypewriterProps) {
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [text, setText] = useState("");
  const [phase, setPhase] = useState<"typing" | "pause" | "deleting">("typing");

  useEffect(() => {
    if (phrases.length === 0) return;
    const current = phrases[phraseIdx % phrases.length];
    let timer: ReturnType<typeof setTimeout>;

    if (phase === "typing") {
      if (text.length < current.length) {
        timer = setTimeout(
          () => setText(current.slice(0, text.length + 1)),
          typeSpeed
        );
      } else {
        timer = setTimeout(() => setPhase("pause"), 50);
      }
    } else if (phase === "pause") {
      timer = setTimeout(() => {
        if (!loop && phraseIdx === phrases.length - 1) return;
        setPhase("deleting");
      }, pauseTime);
    } else {
      if (text.length > 0) {
        timer = setTimeout(
          () => setText(current.slice(0, text.length - 1)),
          deleteSpeed
        );
      } else {
        setPhraseIdx((i) => (i + 1) % phrases.length);
        setPhase("typing");
      }
    }

    return () => clearTimeout(timer);
  }, [text, phase, phraseIdx, phrases, typeSpeed, deleteSpeed, pauseTime, loop]);

  return (
    <span className={className}>
      {text}
      <span className={`animate-pulse ${cursorClassName}`} aria-hidden>
        ▍
      </span>
    </span>
  );
}
