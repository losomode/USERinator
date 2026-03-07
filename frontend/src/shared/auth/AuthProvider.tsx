import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiClient, { setToken, clearToken, getToken } from '../api/client';
import type { Permissions } from '../permissions/types';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  role_level: number;
  company_id: number;
  permissions?: Permissions;
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
      // First get basic user info
      const userResponse = await apiClient.get<User>('/users/me/');
      const userData = userResponse.data;
      
      // Then fetch full context including permissions
      try {
        const contextResponse = await apiClient.get(`/users/${userData.id}/context/`);
        // Merge context data (including permissions) with user data
        setUser({ ...userData, ...contextResponse.data });
      } catch {
        // If context fetch fails, fall back to basic user data
        setUser(userData);
      }
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
