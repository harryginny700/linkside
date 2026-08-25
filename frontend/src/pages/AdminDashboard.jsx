import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Line, LineChart,
} from "recharts";
import { Eye, MousePointerClick, Image as ImageIcon, TrendingUp } from "lucide-react";
import { fetchBanners, fetchOverview, fetchDaily } from "../api";

function StatCard({ icon: Icon, label, value, tone }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className={`flex h-9 w-9 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-3 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

export default function AdminDashboard() {
  const [banners, setBanners] = useState([]);
  const [overview, setOverview] = useState({ totalViews: 0, totalClicks: 0, activeBanners: 0, ctr: 0 });
  const [daily, setDaily] = useState([]);

  useEffect(() => {
    (async () => {
      const [b, o, d] = await Promise.all([fetchBanners(true), fetchOverview(), fetchDaily()]);
      setBanners(b);
      setOverview(o);
      setDaily(d);
    })();
  }, []);

  const topBanners = [...banners].sort((a, b) => b.clicks - a.clicks).slice(0, 5);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-slate-900">İstatistikler</h1>
      <p className="mt-1 text-sm text-slate-500">Reklam performansı genel bakış</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Eye} label="Toplam Görüntülenme" value={overview.totalViews?.toLocaleString()} tone="bg-blue-100 text-blue-600" />
        <StatCard icon={MousePointerClick} label="Toplam Tıklama" value={overview.totalClicks?.toLocaleString()} tone="bg-emerald-100 text-emerald-600" />
        <StatCard icon={ImageIcon} label="Aktif Banner" value={overview.activeBanners} tone="bg-amber-100 text-amber-600" />
        <StatCard icon={TrendingUp} label="Tıklama Oranı (CTR)" value={`%${overview.ctr}`} tone="bg-purple-100 text-purple-600" />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Son 14 Gün</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
              <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <Tooltip />
              <Line type="monotone" dataKey="views" stroke="#3b82f6" strokeWidth={2} dot={false} name="Görüntülenme" />
              <Line type="monotone" dataKey="clicks" stroke="#10b981" strokeWidth={2} dot={false} name="Tıklama" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Banner Bazında Tıklama</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={topBanners} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis type="category" dataKey="title" width={110} tick={{ fontSize: 10, fill: "#64748b" }} />
              <Tooltip />
              <Bar dataKey="clicks" fill="#f59e0b" radius={[0, 4, 4, 0]} name="Tıklama" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-slate-200 bg-white shadow-sm">
        <h2 className="border-b border-slate-100 p-5 text-sm font-semibold text-slate-700">En Çok Tıklanan Bannerlar</h2>
        <div className="divide-y divide-slate-100">
          {topBanners.map((b, i) => (
            <div key={b.id} className="flex items-center gap-4 px-5 py-3">
              <span className="w-5 text-sm font-bold text-slate-400">{i + 1}</span>
              <img src={b.image} alt="" className="h-10 w-16 rounded object-cover" />
              <span className="flex-1 text-sm font-medium text-slate-700">{b.title}</span>
              <span className="text-sm font-semibold text-slate-900">{b.clicks?.toLocaleString()} tıklama</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
