import { createContext, useState, useEffect, useCallback } from "react";
import { authApi } from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is logged in on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      authApi
        .getMe()
        .then((userData) => {
          setUser(userData);
        })
        .catch(() => {
          localStorage.removeItem("token");
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (username, password) => {
    setError(null);
    try {
      const data = await authApi.login(username, password);
      localStorage.setItem("token", data.access_token);
      const userData = await authApi.getMe();
      setUser(userData);
      return userData;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  const register = useCallback(
    async (username, password) => {
      setError(null);
      try {
        await authApi.register(username, password);
        // Auto-login after registration
        return await login(username, password);
      } catch (err) {
        setError(err.message);
        throw err;
      }
    },
    [login],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    clearError,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
