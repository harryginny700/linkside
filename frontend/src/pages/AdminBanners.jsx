import React, { useState, useRef, useEffect } from "react";
import {
  Plus, Pencil, Trash2, ArrowUp, ArrowDown, Upload, Link2,
  ExternalLink, GripVertical,
} from "lucide-react";
import {
  fetchBanners, createBanner, updateBanner, deleteBanner, reorderBanners,
  fetchSettings, saveSettings, uploadImage,
} from "../api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { useToast } from "../hooks/use-toast";

const empty = {
  title: "", image: "", url: "", section: "grid", orient: "square", span: 1, active: true,
};

export default function AdminBanners() {
  const { toast } = useToast();
  const [banners, setBanners] = useState([]);
  const [settings, setSettings] = useState({ gridColumns: 2, ageGateEnabled: true });
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(empty);
  const [uploading, setUploading] = useState(false);
  const [titleInput, setTitleInput] = useState("");
  const fileRef = useRef(null);

  const refresh = async () => setBanners(await fetchBanners(true));

  useEffect(() => {
    (async () => {
      setBanners(await fetchBanners(true));
      const s = await fetchSettings();
      setSettings(s);
      setTitleInput(s.siteTitle || "");
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
    if (!form.image || !form.url) {
      toast({ title: "Eksik bilgi", description: "Görsel ve link zorunludur.", variant: "destructive" });
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

  const saveTitle = async () => {
    await updateSetting({ siteTitle: titleInput });
    toast({ title: "Kaydedildi", description: "Site başlığı güncellendi." });
  };

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

      {/* Layout settings */}
      <div className="mt-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm font-semibold text-slate-800">Site Başlığı</p>
        <p className="text-xs text-slate-500">Tarayıcı sekmesinde görünen başlık</p>
        <div className="mt-3 flex gap-2">
          <Input
            value={titleInput}
            onChange={(e) => setTitleInput(e.target.value)}
            placeholder="Örn. Güvenli Platform"
            className="max-w-md"
          />
          <Button onClick={saveTitle} className="bg-slate-900 hover:bg-slate-800">Kaydet</Button>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-sm font-semibold text-slate-800">Kolon Sayısı (Grid)</p>
            <p className="text-xs text-slate-500">Alt ızgaradaki sütun sayısı</p>
          </div>
          <Select value={String(settings.gridColumns)} onValueChange={(v) => updateSetting({ gridColumns: Number(v) })}>
            <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[1, 2, 3, 4].map((n) => <SelectItem key={n} value={String(n)}>{n} kolon</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <p className="text-sm font-semibold text-slate-800">18+ Yaş Kapısı</p>
            <p className="text-xs text-slate-500">Girişte yaş doğrulama popup'ı</p>
          </div>
          <Switch checked={settings.ageGateEnabled} onCheckedChange={(v) => updateSetting({ ageGateEnabled: v })} />
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Banner Düzenle" : "Yeni Banner"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Başlık</Label>
              <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Banner başlığı" className="mt-1.5" />
            </div>

            <div>
              <Label>Görsel</Label>
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
              {form.image && <img src={form.image} alt="" className="mt-2 h-24 w-full rounded-lg border border-slate-200 object-contain bg-slate-50" />}
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
