import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient, { setToken, clearToken, getToken } from '../api/client';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  role_level: number;
  company_id: number;
}

interface AuthContextType {
  user: User | null;
  isAdmin: boolean;
  isCompanyAdmin: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const response = await apiClient.get<User>('/users/me/');
      setUser(response.data);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  // Check for SSO token in URL params (after OAuth redirect)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    if (token) {
      setToken(token);
      window.history.replaceState({}, '', window.location.pathname);
      fetchCurrentUser();
    }
  }, [fetchCurrentUser]);

  const login = async (username: string, password: string) => {
    const response = await apiClient.post('/auth/login/', { username, password });
    setToken(response.data.access);
    await fetchCurrentUser();
  };

  const logout = () => {
    clearToken();
    setUser(null);
    window.location.href = '/login';
  };

  const isAdmin = (user?.role_level ?? 0) >= 100;
  const isCompanyAdmin = (user?.role_level ?? 0) >= 30;

  return (
    <AuthContext.Provider value={{ user, isAdmin, isCompanyAdmin, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
