import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TOKEN_KEY = "ad_admin_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);
export const isAuthed = () => !!getToken();

const authHeaders = () => ({ Authorization: `Bearer ${getToken()}` });

// ---- Auth ----
export const apiLogin = async (username, password) => {
  const res = await axios.post(`${API}/auth/login`, { username, password });
  setToken(res.data.token);
  return res.data;
};

// ---- Banners ----
export const fetchBanners = async (all = false) => {
  const res = await axios.get(`${API}/banners`, { params: all ? { all: true } : {} });
  return res.data;
};

export const createBanner = async (banner) => {
  const res = await axios.post(`${API}/banners`, banner, { headers: authHeaders() });
  return res.data;
};

export const updateBanner = async (id, patch) => {
  const res = await axios.put(`${API}/banners/${id}`, patch, { headers: authHeaders() });
  return res.data;
};

export const deleteBanner = async (id) => {
  await axios.delete(`${API}/banners/${id}`, { headers: authHeaders() });
};

export const reorderBanners = async (ids) => {
  await axios.post(`${API}/banners/reorder`, { ids }, { headers: authHeaders() });
};

export const clickBanner = async (id) => {
  try {
    await axios.post(`${API}/banners/${id}/click`);
  } catch (e) {
    /* non-blocking */
  }
};

// ---- Settings ----
export const fetchSettings = async () => {
  const res = await axios.get(`${API}/settings`);
  return res.data;
};

export const saveSettings = async (settings) => {
  const res = await axios.put(`${API}/settings`, settings, { headers: authHeaders() });
  return res.data;
};

// ---- Views & Stats ----
export const recordView = async () => {
  try {
    await axios.post(`${API}/view`);
  } catch (e) {
    /* non-blocking */
  }
};

export const fetchOverview = async () => {
  const res = await axios.get(`${API}/stats/overview`, { headers: authHeaders() });
  return res.data;
};

export const fetchDaily = async () => {
  const res = await axios.get(`${API}/stats/daily`, { headers: authHeaders() });
  return res.data;
};

// ---- Upload ----
export const uploadImage = async (file) => {
  const fd = new FormData();
  fd.append("file", file);
  const res = await axios.post(`${API}/upload`, fd, {
    headers: { ...authHeaders(), "Content-Type": "multipart/form-data" },
  });
  return res.data.url;
};
