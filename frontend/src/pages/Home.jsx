import React, { useEffect, useState } from "react";
import { fetchBanners, fetchSettings, recordView, clickBanner } from "../api";

// saray5 paleti (accent boş olan kartlar için otomatik)
const PALETTE = ["#22c55e", "#8a0f28", "#10f4b0", "#facc14", "#3b82f6", "#a78bfa"];
const TOP_ACCENT = "#facc14";

function hexA(hex, alpha) {
  const h = (hex || "#000000").replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  const n = parseInt(full || "000000", 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
}

// saray5 tarzı reklam kartı (birebir DOM yapısı)
function AdCard({ b, accent, isTop, spanStyle, onClick }) {
  const badge = b.badge || (isTop ? "TÜRKİYENİN EN GÜVENİLİR SİTESİ" : "ZİRVE");
  const headline = b.headline || b.title || "";
  const desc = b.description || "";
  const cta = b.ctaText || "TIKLA KAYIT OL";
  const open = () => onClick();
  return (
    <article
      data-testid="ad-card-item"
      role="link"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } }}
      className={`group relative cursor-pointer overflow-hidden rounded-md border transition-all duration-200 ease-out hover:-translate-y-0.5 sm:rounded-lg min-h-[calc(var(--card-h)*0.62)] sm:min-h-[var(--card-h)]`}
      style={{
        "--card-h": "150px",
        ...spanStyle,
        background: "rgb(24, 30, 44)",
        borderColor: hexA(accent, 0.4),
        boxShadow: `${accent} 0px 0px 34px -14px inset`,
      }}
    >
      <span aria-hidden className="pointer-events-none absolute left-1 top-1 h-2 w-2 border-l-2 border-t-2 sm:left-2 sm:top-2 sm:h-3.5 sm:w-3.5" style={{ borderColor: accent }} />
      <span aria-hidden className="pointer-events-none absolute right-1 top-1 h-2 w-2 border-r-2 border-t-2 sm:right-2 sm:top-2 sm:h-3.5 sm:w-3.5" style={{ borderColor: accent }} />
      <span aria-hidden className="pointer-events-none absolute bottom-1 left-1 h-2 w-2 border-b-2 border-l-2 sm:bottom-2 sm:left-2 sm:h-3.5 sm:w-3.5" style={{ borderColor: accent }} />
      <span aria-hidden className="pointer-events-none absolute bottom-1 right-1 h-2 w-2 border-b-2 border-r-2 sm:bottom-2 sm:right-2 sm:h-3.5 sm:w-3.5" style={{ borderColor: accent }} />

      <span aria-hidden className="pointer-events-none absolute inset-0 z-0 overflow-hidden" data-testid="ad-card-effect">
        <span
          className="card-fx-sweep absolute inset-y-0 w-1/3"
          style={{ "--fx-speed": "6s", background: `linear-gradient(90deg, transparent, ${hexA(accent, 0.4)}, transparent)` }}
        />
      </span>

      {badge && (
        <span
          data-testid="ad-card-badge"
          className={`absolute top-0 z-10 left-1/2 -translate-x-1/2 whitespace-nowrap text-[9px] font-black leading-tight tracking-wide text-black sm:text-[10px] sm:tracking-widest ${
            isTop ? "rounded-b px-1.5 py-px sm:px-2 sm:py-0.5" : "px-2.5 pb-1.5 pt-0.5"
          }`}
          style={{
            background: accent,
            clipPath: isTop ? undefined : "polygon(0 0, 100% 0, 100% 100%, 50% 62%, 0 100%)",
          }}
        >
          {badge}
        </span>
      )}

      <div
        className={`relative z-[1] flex h-full flex-col items-center justify-center gap-1 px-2 pb-2 text-center sm:gap-2 sm:px-5 sm:py-6 ${
          isTop ? "pt-5 sm:pt-6" : "pt-7 sm:pt-8"
        }`}
      >
        {b.image && (
          <img
            data-testid="ad-card-logo"
            alt={headline}
            src={b.image}
            loading="lazy"
            className="mb-0.5 max-h-5 w-auto max-w-[85%] object-contain transition-transform duration-200 group-hover:scale-105 sm:mb-1 sm:max-h-9 sm:max-w-[70%]"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
          />
        )}
        {headline && (
          <h3
            data-testid="ad-card-title"
            className={`font-heading font-black uppercase leading-tight tracking-tight text-white ${
              isTop ? "text-[16px] sm:text-2xl" : "text-[13px] sm:text-xl"
            }`}
          >
            {headline}
          </h3>
        )}
        {desc && (
          <p
            data-testid="ad-card-line1"
            className={`font-bold uppercase leading-snug tracking-tight text-slate-100 sm:tracking-wide ${
              isTop ? "text-[12px] sm:text-[13px]" : "text-[10px] sm:text-[11px]"
            }`}
          >
            {desc}
          </p>
        )}
        {cta && (
          <p
            data-testid="ad-card-line2"
            className={`font-bold uppercase leading-snug tracking-tight sm:tracking-wide ${
              isTop ? "text-[12px] sm:text-[13px]" : "text-[10px] sm:text-[11px]"
            }`}
            style={{ color: accent }}
          >
            {cta}
          </p>
        )}
      </div>
    </article>
  );
}

export default function Home() {
  const [settings, setSettings] = useState(null);
  const [banners, setBanners] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [s, b] = await Promise.all([fetchSettings(), fetchBanners(false)]);
        setSettings(s);
        setBanners(b);
        if (s.siteTitle) document.title = s.siteTitle;
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (!loading) recordView();
  }, [loading]);

  const openLink = (b) => {
    clickBanner(b.id);
    window.open(b.url, "_blank", "noopener");
  };

  if (loading) {
    return <div className="site-bg" />;
  }

  const topBanners = banners.filter((b) => b.section === "top");
  const gridBanners = banners.filter((b) => b.section !== "top");
  const cols = Math.min(settings?.gridColumns || 3, 6);
  const brand = settings?.brandName || "EMRE18";
  const ticker = settings?.tickerItems || [];

  return (
    <div className="site-bg flex min-h-screen flex-col">
      {/* Üst duyuru barı (kayan marquee) */}
      <header className="sticky top-0 z-40 border-b border-white/5" style={{ background: "rgb(12, 14, 19)" }}>
        <div className="mx-auto flex h-11 w-full max-w-6xl items-center gap-4 px-3 sm:px-4">
          <span className="shrink-0 text-base font-black italic tracking-tight text-white">{brand}</span>
          {ticker.length > 0 && (
            <div className="relative flex-1 overflow-hidden" data-testid="ticker-marquee">
              <div className="animate-marquee flex w-max items-center gap-8 sm:gap-10">
                {[...ticker, ...ticker].map((t, i) => (
                  <span
                    key={i}
                    className="flex shrink-0 items-center gap-1.5 whitespace-nowrap text-[11px] font-bold tracking-wide"
                    style={{ color: t.color || "#22d3ee" }}
                  >
                    <span aria-hidden>◆</span> {t.text}
                  </span>
                ))}
              </div>
            </div>
          )}
          {settings?.statusLabel && (
            <span
              className="flex shrink-0 items-center gap-1.5 text-[10px] font-bold tracking-widest"
              style={{ color: "rgb(52, 211, 153)" }}
              data-testid="status-pill"
            >
              <span className="h-2 w-2 rounded-full" style={{ background: "rgb(52, 211, 153)" }} />
              {settings.statusLabel}
            </span>
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-3 py-6 sm:px-4 sm:py-8">
        {/* Başlık */}
        <div className="mb-4 flex items-center justify-center gap-3">
          <span className="h-px flex-1" style={{ background: "rgba(245, 158, 11, 0.25)" }} />
          <h1
            data-testid="portal-title"
            className="text-center font-heading text-sm font-black uppercase tracking-[0.2em] sm:text-base"
            style={{ color: "rgb(245, 158, 11)" }}
          >
            {settings?.headerTitle || "EMRE18"}
          </h1>
          <span className="h-px flex-1" style={{ background: "rgba(245, 158, 11, 0.25)" }} />
        </div>
        {settings?.headerSubtitle && (
          <p
            data-testid="portal-tagline"
            className="mb-6 text-center text-[11px] font-bold uppercase tracking-wide"
            style={{ color: "rgb(6, 182, 212)" }}
          >
            {settings.headerSubtitle}
          </p>
        )}

        {/* Reklam grid'i */}
        <div
          className="ad-grid"
          data-testid="ad-grid"
          style={{ "--cols": cols, gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        >
          {topBanners.map((b, i) => (
            <AdCard
              key={b.id}
              b={b}
              accent={b.accent || TOP_ACCENT}
              isTop
              spanStyle={{ gridColumn: "1 / -1" }}
              onClick={() => openLink(b)}
            />
          ))}
          {gridBanners.map((b, i) => (
            <AdCard
              key={b.id}
              b={b}
              accent={b.accent || PALETTE[i % PALETTE.length]}
              isTop={false}
              spanStyle={{ gridColumn: `span ${Math.min(b.span || 1, cols)}` }}
              onClick={() => openLink(b)}
            />
          ))}
        </div>

        <p data-testid="slot-count" className="mt-5 text-center font-mono text-[10px] uppercase tracking-widest text-slate-500">
          {banners.length} aktif reklam alanı
        </p>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center">
        {settings?.footerText && (
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-500">{settings.footerText}</p>
        )}
        {settings?.footerDomains && (
          <p className="mt-2 font-mono text-[10px] tracking-wide text-slate-500">
            Aktif domainleri: <span className="text-slate-300">{settings.footerDomains}</span>
          </p>
        )}
      </footer>
    </div>
  );
}
