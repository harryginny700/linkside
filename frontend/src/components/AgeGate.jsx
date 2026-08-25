import React, { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Button } from "./ui/button";

export default function AgeGate({ onVerified }) {
  const [denied, setDenied] = useState(false);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center site-bg px-4">
      <div className="w-full max-w-lg rounded-2xl border border-amber-500/30 bg-[#1b1b38]/95 p-8 text-center shadow-2xl backdrop-blur">
        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/40 bg-emerald-500/10 px-4 py-1.5 text-xs font-semibold text-emerald-300">
          <ShieldCheck className="h-4 w-4" /> Güvenilir & Doğrulanmış Platform
        </span>

        <h1 className="mt-5 text-2xl font-bold text-white">
          Güvenli ve Güvenilir Bir Platformdasınız
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          You are on a safe &amp; trusted platform
        </p>

        <p className="mt-5 text-sm leading-relaxed text-slate-300">
          Bu platform; güvenlik, gizlilik ve kullanıcı memnuniyeti önceliğiyle
          hizmet vermektedir. Tüm içerikler denetlenmekte ve güvenilirlik
          standartlarına uygun şekilde sunulmaktadır.
        </p>

        <div className="mt-6 flex items-center gap-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-left">
          <span className="text-3xl font-extrabold text-red-400">18+</span>
          <p className="text-xs leading-relaxed text-slate-300">
            Bu yayın yalnızca 18 yaş ve üzeri kullanıcılar tarafından
            görüntülenebilir.
          </p>
        </div>

        <p className="mt-6 font-semibold text-white">
          18 yaşından büyük müsünüz? / Are you over 18?
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <Button
            onClick={onVerified}
            className="h-auto flex-1 flex-col bg-emerald-600 py-3 text-base font-bold hover:bg-emerald-500"
          >
            Evet, 18 yaşından büyüğüm
            <span className="text-xs font-normal opacity-80">Yes, I am over 18</span>
          </Button>
          <Button
            variant="outline"
            onClick={() => setDenied(true)}
            className="h-auto flex-1 flex-col border-slate-600 bg-transparent py-3 text-base font-bold text-slate-200 hover:bg-slate-700/40"
          >
            Hayır
            <span className="text-xs font-normal opacity-70">No</span>
          </Button>
        </div>

        {denied && (
          <div className="mt-4 rounded-lg bg-red-900/40 px-4 py-3 text-sm text-red-200">
            Üzgünüz, bu içeriği görüntüleyebilmek için 18 yaşından büyük olmanız
            gerekmektedir.
          </div>
        )}

        <p className="mt-6 text-[11px] leading-relaxed text-slate-500">
          Bu sayfa, güvenliğiniz için otomatik olarak gösterilmektedir.
        </p>
      </div>
    </div>
  );
}
