import { HeartPulse, ShieldCheck, Brain, Activity, Loader2 } from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "@/hooks/useAuth";

const features = [
  { icon: HeartPulse, title: "AI Health Insights", desc: "Personalized health analysis powered by trusted data" },
  { icon: ShieldCheck, title: "Privacy-First", desc: "Your data stays yours — full control over sharing" },
  { icon: Brain, title: "Smart Suggestions", desc: "Medicine & lifestyle recommendations with doctor warnings" },
  { icon: Activity, title: "Trend Detection", desc: "Anomaly detection across your vitals over time" },
];

declare global {
  interface Window {
    google?: any;
  }
}

type Mode = "signin" | "signup";

export function LoginPage() {
  const { loginEmail, registerEmail, loginGoogle, googleClientId } = useAuth();
  const [mode, setMode] = useState<Mode>("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const googleBtnRef = useRef<HTMLDivElement>(null);

  const handleGoogle = useCallback(
    async (response: { credential?: string }) => {
      if (!response?.credential) return;
      setError(null);
      setBusy(true);
      try {
        await loginGoogle(response.credential);
      } catch (e: any) {
        setError(e?.message || "Google sign-in failed.");
      } finally {
        setBusy(false);
      }
    },
    [loginGoogle],
  );

  /* Load Google Identity Services and render the official button (client-only). */
  useEffect(() => {
    if (!googleClientId || typeof window === "undefined") return;
    let detach: (() => void) | undefined;

    const init = () => {
      if (!window.google?.accounts?.id || !googleBtnRef.current) return;
      window.google.accounts.id.initialize({ client_id: googleClientId, callback: handleGoogle });
      googleBtnRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline",
        size: "large",
        text: mode === "signup" ? "signup_with" : "continue_with",
        shape: "pill",
        width: 320,
      });
    };

    if (window.google?.accounts?.id) {
      init();
      return;
    }
    const SCRIPT_ID = "google-gsi-client";
    let script = document.getElementById(SCRIPT_ID) as HTMLScriptElement | null;
    if (!script) {
      script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
    script.addEventListener("load", init);
    detach = () => script?.removeEventListener("load", init);
    return detach;
  }, [googleClientId, handleGoogle, mode]);

  const submitEmail = async () => {
    setError(null);
    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }
    if (mode === "signup" && password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      if (mode === "signup") {
        await registerEmail(name.trim(), email.trim(), password);
      } else {
        await loginEmail(email.trim(), password);
      }
    } catch (e: any) {
      setError(e?.message || "Authentication failed.");
    } finally {
      setBusy(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submitEmail();
    }
  };

  return (
    <div className="min-h-screen flex" style={{ background: "var(--gradient-bg)", backgroundAttachment: "fixed" }}>
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col justify-center items-center w-1/2 p-12">
        <div className="max-w-md">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-2xl gradient-sage grid place-items-center text-white shadow-lg">
              <HeartPulse className="w-7 h-7" />
            </div>
            <div>
              <h1 className="font-display text-3xl font-bold tracking-tight">Relay-med</h1>
              <p className="text-sm text-muted-foreground">Your AI Health Companion</p>
            </div>
          </div>
          <p className="text-lg text-muted-foreground leading-relaxed mb-8">
            Trust-aware predictive healthcare intelligence — explainable, preventive wellness with personalized AI insights.
          </p>
          <div className="grid grid-cols-2 gap-4">
            {features.map((f) => (
              <div key={f.title} className="soft-card p-4 fade-in">
                <f.icon className="w-5 h-5 text-sage mb-2" />
                <div className="font-semibold text-sm">{f.title}</div>
                <div className="text-[11px] text-muted-foreground leading-relaxed mt-1">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — auth */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="soft-card p-8 w-full max-w-md fade-in">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-11 h-11 rounded-2xl gradient-sage grid place-items-center text-white">
              <HeartPulse className="w-5 h-5" />
            </div>
            <div>
              <div className="font-display text-xl font-semibold">Relay-med</div>
              <div className="text-[11px] text-muted-foreground">Your AI Health Companion</div>
            </div>
          </div>

          <h2 className="font-display text-2xl font-semibold tracking-tight">
            {mode === "signup" ? "Create your account" : "Welcome back"}
          </h2>
          <p className="text-sm text-muted-foreground mt-1 mb-6">
            {mode === "signup"
              ? "Sign up to start your personalized health dashboard"
              : "Sign in to access your personalized health dashboard"}
          </p>

          {error && (
            <div className="mb-4 text-sm rounded-xl border border-red-200 bg-red-50 text-red-700 px-3 py-2">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {/* Google (real OAuth via Google Identity Services) */}
            {googleClientId ? (
              <div ref={googleBtnRef} className="flex justify-center min-h-[44px]" />
            ) : (
              <button
                disabled
                title="Set GOOGLE_CLIENT_ID on the backend to enable Google sign-in"
                className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border bg-white text-sm font-medium opacity-50 cursor-not-allowed"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Google sign-in not configured
              </button>
            )}

            <div className="flex items-center gap-3 my-2">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xs text-muted-foreground">or use email</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {mode === "signup" && (
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Your name"
                disabled={busy}
                className="w-full px-4 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50"
              />
            )}
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Email address"
              type="email"
              autoComplete="email"
              disabled={busy}
              className="w-full px-4 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50"
            />
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={mode === "signup" ? "Create a password (min 8 chars)" : "Password"}
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              disabled={busy}
              className="w-full px-4 py-2.5 rounded-xl border text-sm outline-none focus:ring-2 ring-sage/30 disabled:opacity-50"
            />
            <button
              onClick={submitEmail}
              disabled={busy}
              className="w-full px-4 py-3 rounded-xl gradient-sage text-white text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === "signup" ? "Create account" : "Sign in"}
            </button>
          </div>

          <p className="text-xs text-muted-foreground text-center mt-4">
            {mode === "signup" ? "Already have an account?" : "New to Relay-med?"}{" "}
            <button
              onClick={() => {
                setError(null);
                setMode(mode === "signup" ? "signin" : "signup");
              }}
              className="text-sage font-medium hover:underline"
            >
              {mode === "signup" ? "Sign in" : "Create one"}
            </button>
          </p>

          <p className="text-[10px] text-muted-foreground text-center mt-6 leading-relaxed">
            By continuing, you agree to our Terms of Service and Privacy Policy. Your health data is encrypted and never
            shared without your explicit consent.
          </p>
        </div>
      </div>
    </div>
  );
}
