import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";

interface User {
  id: string;
  name: string;
  email: string;
  avatar: string;
  provider: "google" | "twitter" | "email";
  joined: string;
}

interface AuthContextType {
  user: User | null;
  isLoggedIn: boolean;
  login: (provider: "google" | "twitter" | "email", name?: string, email?: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const STORAGE_KEY = "relaymed_user";

/* Generate a deterministic avatar initial from name */
function getInitial(name: string): string {
  return name.charAt(0).toUpperCase();
}

/* Simulate OAuth login — stores user in localStorage */
function createUser(provider: "google" | "twitter" | "email", name?: string, email?: string): User {
  const defaults: Record<string, { name: string; email: string }> = {
    google: { name: "Shreya", email: "shreya@gmail.com" },
    twitter: { name: "Shreya", email: "shreya@twitter.com" },
    email: { name: name || "User", email: email || "user@relaymed.com" },
  };
  const d = defaults[provider];
  return {
    id: `${provider}_${Date.now()}`,
    name: name || d.name,
    email: email || d.email,
    avatar: getInitial(name || d.name),
    provider,
    joined: new Date().toISOString(),
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  /* Restore session on mount */
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) setUser(JSON.parse(stored));
    } catch { /* ignore corrupt storage */ }
  }, []);

  const login = useCallback((provider: "google" | "twitter" | "email", name?: string, email?: string) => {
    const u = createUser(provider, name, email);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoggedIn: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
