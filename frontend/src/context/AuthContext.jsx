import React, { createContext, useContext, useState } from "react";
import { mockLogin, isAuthed, logout as doLogout } from "../mock";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [authed, setAuthed] = useState(() => isAuthed());

  const login = (username, password) => {
    const res = mockLogin(username, password);
    if (res.success) setAuthed(true);
    return res.success;
  };

  const logout = () => {
    doLogout();
    setAuthed(false);
  };

  return (
    <AuthContext.Provider value={{ authed, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
