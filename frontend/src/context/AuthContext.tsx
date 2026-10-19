import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthResponse, UserRole } from '../types';
import { api } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (allowed: UserRole[]) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('logsentinel_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('logsentinel_token');
      if (storedToken) {
        try {
          const profile = await api.get<User>('/auth/me');
          setUser(profile);
        } catch (err) {
          console.warn('Session expired or token invalid:', err);
          localStorage.removeItem('logsentinel_token');
          setToken(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await api.post<AuthResponse>('/auth/login', { email, password });
    localStorage.setItem('logsentinel_token', data.access_token);
    setToken(data.access_token);
    
    // Fetch full profile
    const profile = await api.get<User>('/auth/me');
    setUser(profile);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (err) {
      console.warn('Backend logout notification skipped or failed:', err);
    } finally {
      localStorage.removeItem('logsentinel_token');
      setToken(null);
      setUser(null);
      window.location.href = '/login';
    }
  };

  const hasRole = (allowed: UserRole[]) => {
    if (!user) return false;
    return allowed.includes(user.role);
  };

  const refreshUser = async () => {
    try {
      const profile = await api.get<User>('/auth/me');
      setUser(profile);
    } catch (err) {
      console.warn('Failed to refresh user profile:', err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
