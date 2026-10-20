import { createContext, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { api } from "../api/client";

interface AuthContextValue {
  token: string | null;
  user: string | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const TOKEN_KEY = "sv_access_token";
const REFRESH_KEY = "sv_refresh_token";
const USER_KEY = "sv_user";

function readStored(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string | null) {
  try {
    if (value) localStorage.setItem(key, value);
    else localStorage.removeItem(key);
  } catch {
    /* ignore quota / private mode */
  }
}

// Sync tokens into the API client before any child effect can fire a request.
const initialAccess = readStored(TOKEN_KEY);
const initialRefresh = readStored(REFRESH_KEY);
if (initialAccess) api.setToken(initialAccess);
if (initialRefresh) api.setRefreshToken(initialRefresh);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => initialAccess);
  const [user, setUser] = useState<string | null>(() => readStored(USER_KEY));

  useEffect(() => {
    api.setToken(token);
    writeStored(TOKEN_KEY, token);
  }, [token]);

  useEffect(() => {
    writeStored(USER_KEY, user);
  }, [user]);

  useEffect(() => {
    api.setUnauthorizedHandler(() => {
      setToken(null);
      setUser(null);
      writeStored(TOKEN_KEY, null);
      writeStored(REFRESH_KEY, null);
      writeStored(USER_KEY, null);
      api.setRefreshToken(null);
    });
    api.setTokensUpdatedHandler((access, refresh) => {
      setToken(access);
      writeStored(TOKEN_KEY, access);
      if (refresh) {
        api.setRefreshToken(refresh);
        writeStored(REFRESH_KEY, refresh);
      }
    });
    return () => {
      api.setUnauthorizedHandler(null);
      api.setTokensUpdatedHandler(null);
    };
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login: async (username: string, password: string) => {
        const pair = await api.login(username, password);
        api.setToken(pair.access);
        api.setRefreshToken(pair.refresh);
        writeStored(TOKEN_KEY, pair.access);
        writeStored(REFRESH_KEY, pair.refresh);
        setToken(pair.access);
        setUser(username);
      },
      logout: () => {
        setToken(null);
        setUser(null);
        api.setToken(null);
        api.setRefreshToken(null);
        writeStored(TOKEN_KEY, null);
        writeStored(REFRESH_KEY, null);
        writeStored(USER_KEY, null);
      },
    }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
