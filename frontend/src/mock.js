// Mock data + localStorage persistence layer.
// This simulates the backend so the frontend feels fully functional.
// Later this will be replaced by real API calls (see contracts.md).

const LS_BANNERS = "ad_banners";
const LS_SETTINGS = "ad_settings";
const LS_STATS = "ad_stats";
const LS_AUTH = "ad_admin_token";

// ---- Seed data (mirrors the reference kara8.com layout) ----
const seedBanners = [
  {
    id: "b1",
    section: "top", // top wide banner group
    image: "https://kara8.com/uploads/banners/6a861dbf85213.jpg",
    url: "https://sloganbahis.click/?refId=39",
    title: "SloganBahis 8000TL",
    orient: "wide",
    span: 2,
    order: 0,
    active: true,
    clicks: 1284,
  },
  {
    id: "c1",
    section: "grid",
    image: "https://kara8.com/uploads/bonus_cards/6a861d9e2fcb1.png",
    url: "https://sloganbahis.click/?refId=39",
    title: "SloganBahis 8.000TL Nakit",
    orient: "square",
    span: 1,
    order: 1,
    active: true,
    clicks: 642,
  },
  {
    id: "c2",
    section: "grid",
    image: "https://kara8.com/uploads/bonus_cards/6a6788c39b25c.jpg",
    url: "https://jiletbahisaffiliate.com/redirect-1/fici-aff",
    title: "JiletBahis 20 Bin Yatır",
    orient: "square",
    span: 1,
    order: 2,
    active: true,
    clicks: 531,
  },
  {
    id: "c3",
    section: "grid",
    image: "https://kara8.com/uploads/bonus_cards/6a5f512316d09.png",
    url: "https://kisal.site/padisah",
    title: "MilanBahis 3.000TL Deneme",
    orient: "square",
    span: 1,
    order: 3,
    active: true,
    clicks: 418,
  },
  {
    id: "c4",
    section: "grid",
    image: "https://kara8.com/uploads/bonus_cards/6a8cb64dc0b3d.jpg",
    url: "https://t2m.co/padiisah",
    title: "HerkulBet 3000TL Deneme",
    orient: "square",
    span: 1,
    order: 4,
    active: true,
    clicks: 377,
  },
];

const seedSettings = {
  siteTitle: "Güvenli Platform",
  gridColumns: 2, // number of columns in the bonus grid
  ageGateEnabled: true,
  totalViews: 8421,
};

function genDailyStats() {
  const days = [];
  const today = new Date();
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    days.push({
      date: d.toISOString().slice(5, 10),
      views: Math.floor(200 + Math.random() * 500),
      clicks: Math.floor(80 + Math.random() * 260),
    });
  }
  return days;
}

// ---- Init ----
function init() {
  if (!localStorage.getItem(LS_BANNERS)) {
    localStorage.setItem(LS_BANNERS, JSON.stringify(seedBanners));
  }
  if (!localStorage.getItem(LS_SETTINGS)) {
    localStorage.setItem(LS_SETTINGS, JSON.stringify(seedSettings));
  }
  if (!localStorage.getItem(LS_STATS)) {
    localStorage.setItem(LS_STATS, JSON.stringify(genDailyStats()));
  }
}
init();

// ---- Banner helpers ----
export const getBanners = () =>
  JSON.parse(localStorage.getItem(LS_BANNERS) || "[]").sort(
    (a, b) => a.order - b.order
  );

export const saveBanners = (banners) =>
  localStorage.setItem(LS_BANNERS, JSON.stringify(banners));

export const addBanner = (banner) => {
  const banners = getBanners();
  const id = "x" + Date.now();
  const maxOrder = banners.reduce((m, b) => Math.max(m, b.order), 0);
  const nb = { ...banner, id, order: maxOrder + 1, clicks: 0 };
  banners.push(nb);
  saveBanners(banners);
  return nb;
};

export const updateBanner = (id, patch) => {
  const banners = getBanners().map((b) =>
    b.id === id ? { ...b, ...patch } : b
  );
  saveBanners(banners);
};

export const deleteBanner = (id) => {
  saveBanners(getBanners().filter((b) => b.id !== id));
};

export const recordClick = (id) => {
  updateBanner(id, {
    clicks: (getBanners().find((b) => b.id === id)?.clicks || 0) + 1,
  });
};

// ---- Settings ----
export const getSettings = () =>
  JSON.parse(localStorage.getItem(LS_SETTINGS) || "{}");

export const saveSettings = (s) =>
  localStorage.setItem(LS_SETTINGS, JSON.stringify(s));

export const recordView = () => {
  const s = getSettings();
  s.totalViews = (s.totalViews || 0) + 1;
  saveSettings(s);
};

// ---- Stats ----
export const getDailyStats = () =>
  JSON.parse(localStorage.getItem(LS_STATS) || "[]");

// ---- Auth (mock) ----
export const ADMIN_USER = "admin";
export const ADMIN_PASS = "admin123";

export const mockLogin = (username, password) => {
  if (username === ADMIN_USER && password === ADMIN_PASS) {
    const token = "mock-token-" + Date.now();
    localStorage.setItem(LS_AUTH, token);
    return { success: true, token };
  }
  return { success: false };
};

export const isAuthed = () => !!localStorage.getItem(LS_AUTH);
export const logout = () => localStorage.removeItem(LS_AUTH);
