import React, { useEffect, useRef, useState } from "react";
import "./Openingscreen.css";

// Staggered heights + direction for the ambient ticker field behind the logo.
// "down" bars render red, "up" bars render green — like a live price ticker.
const TICKER_BARS = [
  { h: 22, dir: "up" }, { h: 38, dir: "up" }, { h: 16, dir: "down" }, { h: 44, dir: "up" },
  { h: 30, dir: "down" }, { h: 52, dir: "up" }, { h: 24, dir: "down" }, { h: 41, dir: "up" },
  { h: 18, dir: "up" }, { h: 47, dir: "down" }, { h: 33, dir: "up" }, { h: 55, dir: "up" },
  { h: 20, dir: "down" }, { h: 43, dir: "up" }, { h: 29, dir: "down" }, { h: 50, dir: "up" },
  { h: 26, dir: "up" }, { h: 39, dir: "down" }, { h: 17, dir: "up" }, { h: 46, dir: "down" },
  { h: 32, dir: "up" }, { h: 54, dir: "up" }, { h: 23, dir: "down" }, { h: 40, dir: "up" },
];

export default function OpeningScreen({
  appName,
  tagline,
  duration = 1800,
  onFinish = () => {},
}) {
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);
  const startRef = useRef(null);
  const rafRef = useRef(null);

  useEffect(() => {
    startRef.current = performance.now();
    const tick = (now) => {
      const elapsed = now - startRef.current;
      const pct = Math.min(100, (elapsed / duration) * 100);
      setProgress(pct);
      if (pct < 100) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setExiting(true);
        setTimeout(onFinish, 650);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [duration, onFinish]);

  const dashTotal = 520;
  const dashOffset = dashTotal - (dashTotal * progress) / 100;

  return (
    <div className={`os-root${exiting ? " os-exit" : ""}`}>
      <div className="os-grid" aria-hidden="true" />
      <div className="os-ticker" aria-hidden="true">
        {TICKER_BARS.map((bar, i) => (
          <span
            key={i}
            className={bar.dir}
            style={{ height: `${bar.h}%`, animationDelay: `${(i % 8) * 0.15}s` }}
          />
        ))}
      </div>

      <div className="os-center">
        <svg className="os-mark" viewBox="0 0 56 56" aria-hidden="true">
          <line x1="14" y1="6" x2="14" y2="50" stroke="rgba(159,255,172,0.45)" strokeWidth="1.5" />
          <rect x="9" y="22" width="10" height="16" rx="1.5" fill="#234d24" />
          <line x1="28" y1="2" x2="28" y2="54" stroke="rgba(159,255,172,0.45)" strokeWidth="1.5" />
          <rect x="23" y="10" width="10" height="30" rx="1.5" fill="#479a4b" />
          <line x1="42" y1="14" x2="42" y2="46" stroke="rgba(159,255,172,0.45)" strokeWidth="1.5" />
          <rect x="37" y="24" width="10" height="14" rx="1.5" fill="#9fffac" />
        </svg>

        <h1 className="os-word">{appName}</h1>
        <p className="os-tag">{tagline}</p>

        <svg className="os-chart" viewBox="0 0 220 44" preserveAspectRatio="none" aria-hidden="true">
          <path
            d="M2,36 L24,30 L46,34 L68,20 L90,24 L112,10 L134,16 L156,6 L178,12 L200,3 L218,8"
            strokeDasharray={dashTotal}
            strokeDashoffset={dashOffset}
          />
        </svg>
      </div>
    </div>
  );
}
