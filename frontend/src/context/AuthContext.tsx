import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi } from "../services/api";

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ user: null, token: null, loading: true });

  useEffect(() => {
    const token = localStorage.getItem("cl_token");
    const userStr = localStorage.getItem("cl_user");
    if (token && userStr) {
      try {
        setState({ user: JSON.parse(userStr), token, loading: false });
      } catch {
        localStorage.removeItem("cl_token");
        localStorage.removeItem("cl_user");
        setState({ user: null, token: null, loading: false });
      }
    } else {
      setState(s => ({ ...s, loading: false }));
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    localStorage.setItem("cl_token", data.access_token);
    localStorage.setItem("cl_user", JSON.stringify(data.user));
    setState({ user: data.user, token: data.access_token, loading: false });
  }, []);

  const signup = useCallback(async (email: string, username: string, password: string, fullName?: string) => {
    const data = await authApi.signup(email, username, password, fullName);
    localStorage.setItem("cl_token", data.access_token);
    localStorage.setItem("cl_user", JSON.stringify(data.user));
    setState({ user: data.user, token: data.access_token, loading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("cl_token");
    localStorage.removeItem("cl_user");
    setState({ user: null, token: null, loading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
