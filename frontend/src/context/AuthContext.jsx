import React, { createContext, useContext, useState } from "react";
import { apiLogin, isAuthed, clearToken } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [authed, setAuthed] = useState(() => isAuthed());

  const login = async (username, password) => {
    try {
      await apiLogin(username, password);
      setAuthed(true);
      return true;
    } catch (e) {
      return false;
    }
  };

  const logout = () => {
    clearToken();
    setAuthed(false);
  };

  return (
    <AuthContext.Provider value={{ authed, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
