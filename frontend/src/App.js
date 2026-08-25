import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { Toaster } from "./components/ui/toaster";
import Home from "./pages/Home";
import AdminLogin from "./pages/AdminLogin";
import AdminLayout from "./components/AdminLayout";
import AdminDashboard from "./pages/AdminDashboard";
import AdminBanners from "./pages/AdminBanners";

function Protected({ children }) {
  const { authed } = useAuth();
  return authed ? children : <Navigate to="/admin" replace />;
}

function AdminEntry() {
  const { authed } = useAuth();
  return authed ? <Navigate to="/admin/dashboard" replace /> : <AdminLogin />;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/admin" element={<AdminEntry />} />
            <Route
              path="/admin"
              element={
                <Protected>
                  <AdminLayout />
                </Protected>
              }
            >
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="banners" element={<AdminBanners />} />
            </Route>
          </Routes>
          <Toaster />
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
