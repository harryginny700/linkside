import React, { useEffect, useState } from "react";
import AgeGate from "../components/AgeGate";
import {
  getBanners,
  getSettings,
  recordClick,
  recordView,
} from "../mock";

export default function Home() {
  const settings = getSettings();
  const [verified, setVerified] = useState(
    () => !settings.ageGateEnabled || sessionStorage.getItem("age_ok") === "1"
  );
  const [banners] = useState(() => getBanners().filter((b) => b.active));

  useEffect(() => {
    if (verified) recordView();
  }, [verified]);

  const handleVerify = () => {
    sessionStorage.setItem("age_ok", "1");
    setVerified(true);
  };

  const openLink = (b) => {
    recordClick(b.id);
    window.open(b.url, "_blank", "noopener");
  };

  const topBanners = banners.filter((b) => b.section === "top");
  const gridBanners = banners.filter((b) => b.section === "grid");
  const cols = settings.gridColumns || 2;

  if (!verified) return <AgeGate onVerified={handleVerify} />;

  return (
    <div className="site-bg py-8">
      <div className="mx-auto w-full max-w-[1120px] px-3">
        {/* Top banner group */}
        <div className="space-y-4">
          {topBanners.map((b) => (
            <button
              key={b.id}
              onClick={() => openLink(b)}
              className="banner-hover block w-full overflow-hidden rounded-xl border-2 border-amber-500/40"
            >
              <img
                src={b.image}
                alt={b.title}
                loading="lazy"
                className="h-auto w-full object-cover"
              />
            </button>
          ))}
        </div>

        {/* Bonus grid */}
        <div
          className="mt-4 grid gap-4"
          style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        >
          {gridBanners.map((b) => (
            <button
              key={b.id}
              onClick={() => openLink(b)}
              className="banner-hover block overflow-hidden rounded-xl border-2 border-amber-500/40"
              style={{ gridColumn: `span ${Math.min(b.span || 1, cols)}` }}
            >
              <img
                src={b.image}
                alt={b.title}
                loading="lazy"
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>

        <p className="mt-10 text-center text-xs text-slate-500">
          Bu platform güvenliğiniz için içerikleri denetler. 18+
        </p>
      </div>
    </div>
  );
}
