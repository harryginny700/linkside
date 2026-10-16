import React, { useState, useRef, useEffect } from "react";
import {
  Plus, Pencil, Trash2, ArrowUp, ArrowDown, Upload, Link2,
  ExternalLink, GripVertical, X,
} from "lucide-react";
import {
  fetchBanners, createBanner, updateBanner, deleteBanner, reorderBanners,
  fetchSettings, saveSettings, uploadImage,
} from "../api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Slider } from "../components/ui/slider";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { useToast } from "../hooks/use-toast";

const empty = {
  title: "", image: "", url: "", section: "grid", orient: "square", span: 1, active: true,
  badge: "", headline: "", description: "", ctaText: "TIKLA KAYIT OL", accent: "",
};

export default function AdminBanners() {
  const { toast } = useToast();
  const [banners, setBanners] = useState([]);
  const [settings, setSettings] = useState({ gridColumns: 3 });
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);
  const [uploading, setUploading] = useState(false);
  const [logoSize, setLogoSize] = useState(36);
  const logoSizeTimer = useRef(null);
  const fileRef = useRef(null);

  const refresh = async () => setBanners(await fetchBanners(true));

  useEffect(() => {
    (async () => {
      setBanners(await fetchBanners(true));
      const s = await fetchSettings();
      setSettings(s);
      setLogoSize(Number(s.logoSize) || 36);
    })();
  }, []);

  const openNew = () => { setEditing(null); setForm(empty); setOpen(true); };
  const openEdit = (b) => { setEditing(b); setForm(b); setOpen(true); };

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const url = await uploadImage(file);
      setForm((f) => ({ ...f, image: url }));
    } catch (err) {
      toast({ title: "Yükleme hatası", description: "Görsel yüklenemedi.", variant: "destructive" });
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    if (!form.url) {
      toast({ title: "Eksik bilgi", description: "Hedef link zorunludur.", variant: "destructive" });
      return;
    }
    try {
      if (editing) {
        const { id, clicks, order, ...patch } = form;
        await updateBanner(editing.id, patch);
        toast({ title: "Güncellendi", description: "Banner güncellendi." });
      } else {
        await createBanner(form);
        toast({ title: "Eklendi", description: "Yeni banner eklendi." });
      }
      await refresh();
      setOpen(false);
    } catch (err) {
      toast({ title: "Hata", description: "İşlem başarısız.", variant: "destructive" });
    }
  };

  const handleDelete = async (id) => {
    await deleteBanner(id);
    await refresh();
    toast({ title: "Silindi", description: "Banner silindi." });
  };

  const toggleActive = async (b) => {
    await updateBanner(b.id, { active: !b.active });
    await refresh();
  };

  const move = async (index, dir) => {
    const arr = [...banners];
    const target = index + dir;
    if (target < 0 || target >= arr.length) return;
    [arr[index], arr[target]] = [arr[target], arr[index]];
    setBanners(arr);
    await reorderBanners(arr.map((b) => b.id));
    await refresh();
  };

  const updateSetting = async (patch) => {
    const s = { ...settings, ...patch };
    setSettings(s);
    await saveSettings(s);
  };

  // Site görünümü: yerel düzenleme + tek butonla kaydetme
  const setViewField = (patch) => setSettings((s) => ({ ...s, ...patch }));
  const saveView = async () => {
    try {
      await saveSettings(settings);
      toast({ title: "Kaydedildi", description: "Site görünümü güncellendi." });
    } catch (err) {
      toast({ title: "Hata", description: "Ayarlar kaydedilemedi.", variant: "destructive" });
    }
  };

  // Kart logo boyutu: slider + gecikmeli otomatik kayıt
  const handleLogoSizeChange = (val) => {
    const v = Math.round(Math.min(140, Math.max(16, Array.isArray(val) ? val[0] : val)));
    setLogoSize(v);
    setSettings((s) => ({ ...s, logoSize: v }));
    if (logoSizeTimer.current) clearTimeout(logoSizeTimer.current);
    logoSizeTimer.current = setTimeout(async () => {
      try {
        await saveSettings({ logoSize: v });
        toast({ title: "Kaydedildi", description: `Logo boyutu: ${v}px` });
      } catch (err) {
        toast({ title: "Hata", description: "Logo boyutu kaydedilemedi.", variant: "destructive" });
      }
    }, 600);
  };
  const adjustLogoSize = (delta) => handleLogoSizeChange(logoSize + delta);

  const addTicker = () => setSettings((s) => ({
    ...s,
    tickerItems: [...(s.tickerItems || []), { text: "", color: "#22d3ee" }],
  }));
  const updateTicker = (i, patch) => setSettings((s) => ({
    ...s,
    tickerItems: (s.tickerItems || []).map((t, j) => (j === i ? { ...t, ...patch } : t)),
  }));
  const removeTicker = (i) => setSettings((s) => ({
    ...s,
    tickerItems: (s.tickerItems || []).filter((_, j) => j !== i),
  }));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Bannerlar & Kolonlar</h1>
          <p className="mt-1 text-sm text-slate-500">Görselleri, linkleri ve kolon düzenini yönetin</p>
        </div>
        <Button onClick={openNew} className="gap-2 bg-slate-900 hover:bg-slate-800">
          <Plus className="h-4 w-4" /> Yeni Banner
        </Button>
      </div>

      {/* Site görünümü ayarları */}
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-slate-800">Site Görünümü</p>
            <p className="text-xs text-slate-500">Marka, başlık, duyuru barı ve footer metinleri</p>
          </div>
          <Button onClick={saveView} className="bg-slate-900 hover:bg-slate-800">Kaydet</Button>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Label>Marka Adı (üst bar logosu)</Label>
            <Input value={settings.brandName || ""} onChange={(e) => setViewField({ brandName: e.target.value })} placeholder="EMRE18" className="mt-1.5" />
          </div>
          <div>
            <Label>Üst Bar Durum Etiketi</Label>
            <Input value={settings.statusLabel || ""} onChange={(e) => setViewField({ statusLabel: e.target.value })} placeholder="GÜNCEL" className="mt-1.5" />
          </div>
          <div>
            <Label>Başlık (altın renkli)</Label>
            <Input value={settings.headerTitle || ""} onChange={(e) => setViewField({ headerTitle: e.target.value })} placeholder="EMRE18" className="mt-1.5" />
          </div>
          <div>
            <Label>Alt Başlık (mavi)</Label>
            <Input value={settings.headerSubtitle || ""} onChange={(e) => setViewField({ headerSubtitle: e.target.value })} placeholder="GÜNCEL GİRİŞ VE REKLAM ALANLARI" className="mt-1.5" />
          </div>
          <div>
            <Label>Site Başlığı (tarayıcı sekmesi)</Label>
            <Input value={settings.siteTitle || ""} onChange={(e) => setViewField({ siteTitle: e.target.value })} placeholder="Emre18 — Güncel Giriş" className="mt-1.5" />
          </div>
          <div>
            <Label>Aktif Domainler</Label>
            <Input value={settings.footerDomains || ""} onChange={(e) => setViewField({ footerDomains: e.target.value })} placeholder="emre18.com" className="mt-1.5" />
          </div>
          <div className="md:col-span-2">
            <Label>Footer Metni</Label>
            <Input value={settings.footerText || ""} onChange={(e) => setViewField({ footerText: e.target.value })} placeholder="© 2026 EMRE18" className="mt-1.5" />
          </div>
        </div>

        {/* Duyuru barı öğeleri */}
        <div className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-700">Duyuru Barı Öğeleri</p>
            <Button variant="outline" size="sm" onClick={addTicker} className="gap-1">
              <Plus className="h-3.5 w-3.5" /> Ekle
            </Button>
          </div>
          <div className="mt-3 space-y-2">
            {(settings.tickerItems || []).map((t, i) => (
              <div key={i} className="flex items-center gap-2">
                <Input value={t.text || ""} onChange={(e) => updateTicker(i, { text: e.target.value })} placeholder="Duyuru metni" />
                <input
                  type="color"
                  value={t.color || "#22d3ee"}
                  onChange={(e) => updateTicker(i, { color: e.target.value })}
                  className="h-9 w-10 shrink-0 cursor-pointer rounded border border-slate-200 bg-white"
                  title="Renk"
                />
                <Button variant="outline" size="icon" onClick={() => removeTicker(i)} className="shrink-0 text-red-600 hover:bg-red-50">
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            {!(settings.tickerItems || []).length && (
              <p className="text-xs text-slate-400">Öğe yok — Ekle butonu ile duyuru ekleyin.</p>
            )}
          </div>
        </div>
      </div>

      {/* Kolon sayısı + logo boyutu */}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-sm font-semibold text-slate-800">Kolon Sayısı (Grid)</p>
            <p className="text-xs text-slate-500">Alt ızgaradaki sütun sayısı</p>
          </div>
          <Select value={String(settings.gridColumns || 3)} onValueChange={(v) => updateSetting({ gridColumns: Number(v) })}>
            <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4].map((n) => <SelectItem key={n} value={String(n)}>{n} kolon</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-sm font-semibold text-slate-800">Kart Logo Boyutu</p>
            <p className="text-xs text-slate-500">Kartlardaki görsel yüksekliği</p>
            <p className="mt-1 font-mono text-lg font-bold text-slate-800" data-testid="logo-size-label">{logoSize}px</p>
          </div>
          <div className="flex w-36 items-center gap-2 sm:w-44">
            <Button type="button" variant="outline" size="icon" onClick={() => adjustLogoSize(-4)} className="shrink-0 text-base">−</Button>
            <Slider
              value={[logoSize]}
              min={16}
              max={140}
              step={2}
              onValueChange={handleLogoSizeChange}
              data-testid="logo-size-slider"
            />
            <Button type="button" variant="outline" size="icon" onClick={() => adjustLogoSize(4)} className="shrink-0 text-base">+</Button>
          </div>
        </div>
      </div>

      {/* Banner list */}
      <div className="mt-6 space-y-3">
        {banners.map((b, i) => (
          <div key={b.id} className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div className="flex flex-col">
              <button onClick={() => move(i, -1)} className="text-slate-400 hover:text-slate-700"><ArrowUp className="h-4 w-4" /></button>
              <GripVertical className="h-4 w-4 text-slate-300" />
              <button onClick={() => move(i, 1)} className="text-slate-400 hover:text-slate-700"><ArrowDown className="h-4 w-4" /></button>
            </div>
            <img src={b.image} alt="" className="h-14 w-24 rounded-lg border border-slate-200 object-cover" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800">{b.title || "(başlıksız)"}</p>
              <a href={b.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 truncate text-xs text-blue-600 hover:underline">
                <ExternalLink className="h-3 w-3" /> {b.url}
              </a>
              <div className="mt-1 flex gap-2">
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">{b.section === "top" ? "Üst Banner" : "Grid"}</span>
                <span className="flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: b.accent || "#94a3b8" }} /> tema
                </span>
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">{b.orient} · {b.span} kolon</span>
                <span className="rounded bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-600">{b.clicks} tıklama</span>
              </div>
            </div>
            <Switch checked={b.active} onCheckedChange={() => toggleActive(b)} />
            <Button variant="outline" size="icon" onClick={() => openEdit(b)}><Pencil className="h-4 w-4" /></Button>
            <Button variant="outline" size="icon" onClick={() => handleDelete(b.id)} className="text-red-600 hover:bg-red-50"><Trash2 className="h-4 w-4" /></Button>
          </div>
        ))}
      </div>

      {/* Add/Edit dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editing ? "Banner Düzenle" : "Yeni Banner"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Başlık</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Banner başlığı" className="mt-1.5" />
            </div>

            <div>
              <Label>Kart Görseli (Logo)</Label>
              <p className="text-[11px] text-slate-400">Kartta logo olarak görünür. Yükle ile dosya seçin veya görsel URL girin.</p>
              <div className="mt-1.5 flex gap-2">
                <div className="relative flex-1">
                  <Link2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input value={form.image?.startsWith("data:") ? "(yüklenen dosya)" : form.image} onChange={(e) => setForm({ ...form, image: e.target.value })} placeholder="Görsel URL" className="pl-9" disabled={form.image?.startsWith("data:")} />
                </div>
                <Button type="button" variant="outline" onClick={() => fileRef.current?.click()} disabled={uploading} className="gap-2">
                  <Upload className="h-4 w-4" /> {uploading ? "Yükleniyor..." : "Yükle"}
                </Button>
                <input ref={fileRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />
              </div>
              {form.image && (
                <div className="mt-2 flex items-center justify-center rounded-lg border border-slate-200 bg-slate-50 py-3">
                  <img src={form.image} alt="" className="max-h-9 w-auto max-w-[70%] object-contain" />
                </div>
              )}
            </div>

            <div>
              <Label>Hedef Link (URL)</Label>
              <Input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="https://..." className="mt-1.5" />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <Label>Bölüm</Label>
                <Select value={form.section} onValueChange={(v) => setForm({ ...form, section: v })}>
                  <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="top">Üst Banner</SelectItem>
                    <SelectItem value="grid">Grid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Yön</Label>
                <Select value={form.orient} onValueChange={(v) => setForm({ ...form, orient: v })}>
                  <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="square">Kare</SelectItem>
                    <SelectItem value="wide">Geniş</SelectItem>
                    <SelectItem value="tall">Uzun</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Kolon Genişliği</Label>
                <Select value={String(form.span)} onValueChange={(v) => setForm({ ...form, span: Number(v) })}>
                  <SelectTrigger className="mt-1.5"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {[1, 2, 3, 4].map((n) => <SelectItem key={n} value={String(n)}>{n}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold text-slate-700">Kart İçeriği (Yeni Tasarım)</p>
              <p className="text-[11px] text-slate-400">Boş bırakılan alanlarda varsayılanlar kullanılır.</p>
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div>
                  <Label>Rozet</Label>
                  <Input value={form.badge} onChange={(e) => setForm({ ...form, badge: e.target.value })} placeholder="ZİRVE" className="mt-1.5" />
                </div>
                <div>
                  <Label>CTA Metni</Label>
                  <Input value={form.ctaText} onChange={(e) => setForm({ ...form, ctaText: e.target.value })} placeholder="TIKLA KAYIT OL" className="mt-1.5" />
                </div>
                <div className="col-span-2">
                  <Label>Büyük Başlık</Label>
                  <Input value={form.headline} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder="3000₺ NAKİT DENEME BONUSU" className="mt-1.5" />
                </div>
                <div className="col-span-2">
                  <Label>Açıklama</Label>
                  <Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="SINIRSIZ ANLIK ÇEKİM İMKANI" className="mt-1.5" />
                </div>
                <div className="col-span-2">
                  <Label>Tema Rengi</Label>
                  <div className="mt-1.5 flex items-center gap-2">
                    <input
                      type="color"
                      value={form.accent || "#22c55e"}
                      onChange={(e) => setForm({ ...form, accent: e.target.value })}
                      className="h-9 w-12 shrink-0 cursor-pointer rounded border border-slate-200 bg-white"
                      title="Renk seç"
                    />
                    <Input value={form.accent} onChange={(e) => setForm({ ...form, accent: e.target.value })} placeholder="Otomatik (boş bırak)" />
                    <Button type="button" variant="outline" onClick={() => setForm({ ...form, accent: "" })}>Otomatik</Button>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Switch checked={form.active} onCheckedChange={(v) => setForm({ ...form, active: v })} />
              <Label className="cursor-pointer">Aktif (sitede görünür)</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>İptal</Button>
            <Button onClick={handleSave} className="bg-slate-900 hover:bg-slate-800">Kaydet</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
