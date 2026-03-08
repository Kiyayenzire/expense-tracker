

// src/context/AuthContext.jsx

import { createContext, useState, useEffect } from "react";
import { getCurrentUser, logout as logoutService } from "../services/authService";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {

    const loadUser = async () => {

      const token = localStorage.getItem("access");

      if (!token) {
        setLoading(false);
        return;
      }

      try {

        const userData = await getCurrentUser();
        setUser(userData);

      } catch {

        logout();

      }

      setLoading(false);

    };

    loadUser();

  }, []);

  const login = (data) => {

    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);

    setUser(data.user);

  };

  const logout = () => {

    logoutService();
    setUser(null);

  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );

};


