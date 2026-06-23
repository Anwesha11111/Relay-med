import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";
import { apiGet, apiPost } from "@/lib/api";

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  provider: "google" | "twitter" | "email" | string;
  picture?: string | null;
  joined: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoggedIn: boolean;
  loading: boolean;
  googleClientId: string | null;
  loginEmail: (email: string, password: string) => Promise<void>;
  registerEmail: (name: string, email: string, password: string) => Promise<void>;
  loginGoogle: (credential: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const TOKEN_KEY = "relaymed_token";
const USER_KEY = "relaymed_user";

function readStored<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [googleClientId, setGoogleClientId] = useState<string | null>(null);

  /* Restore + validate session on mount (client only). */
  useEffect(() => {
    let cancelled = false;

    (async () => {
      // Discover which providers the backend has enabled.
      try {
        const cfg = await apiGet<{ google_client_id: string | null }>("/api/v1/auth/config");
        if (!cancelled) setGoogleClientId(cfg.google_client_id ?? null);
      } catch {
        /* backend may be down — Google button just stays hidden */
      }

      const storedToken = localStorage.getItem(TOKEN_KEY);
      const cachedUser = readStored<User>(USER_KEY);
      if (storedToken) {
        setToken(storedToken);
        if (cachedUser) setUser(cachedUser); // optimistic, avoids a flash
        try {
          const res = await apiGet<{ user: User }>("/api/v1/auth/me", storedToken);
          if (!cancelled) {
            setUser(res.user);
            localStorage.setItem(USER_KEY, JSON.stringify(res.user));
          }
        } catch (err: any) {
          // Only force logout on a real auth rejection; tolerate transient/offline errors.
          if (!cancelled && /401|expired|signature|token|unknown user/i.test(String(err?.message))) {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            setToken(null);
            setUser(null);
          }
        }
      }
      if (!cancelled) setLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const persist = useCallback((tok: string, u: User) => {
    localStorage.setItem(TOKEN_KEY, tok);
    localStorage.setItem(USER_KEY, JSON.stringify(u));
    setToken(tok);
    setUser(u);
  }, []);

  const loginEmail = useCallback(
    async (email: string, password: string) => {
      const res = await apiPost<{ token: string; user: User }>("/api/v1/auth/login", { email, password });
      persist(res.token, res.user);
    },
    [persist],
  );

  const registerEmail = useCallback(
    async (name: string, email: string, password: string) => {
      const res = await apiPost<{ token: string; user: User }>("/api/v1/auth/register", {
        name,
        email,
        password,
      });
      persist(res.token, res.user);
    },
    [persist],
  );

  const loginGoogle = useCallback(
    async (credential: string) => {
      const res = await apiPost<{ token: string; user: User }>("/api/v1/auth/google", { credential });
      persist(res.token, res.user);
    },
    [persist],
  );

  const logout = useCallback(() => {
    const tok = token;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
    // Best-effort audit; ignore result.
    if (tok) apiPost("/api/v1/auth/logout", undefined, tok).catch(() => {});
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoggedIn: !!user && !!token,
        loading,
        googleClientId,
        loginEmail,
        registerEmail,
        loginGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
