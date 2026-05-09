import { Link, useLocation } from "@tanstack/react-router";
import {
  LayoutDashboard,
  HeartPulse,
  Sparkles,
  GitBranch,
  FlaskConical,
  Bell,
  MessageCircle,
  FileText,
  BookOpen,
  ShieldCheck,
  Settings,
  Gem,
  ChevronRight,
  LogOut,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useNotifications } from "@/hooks/useNotifications";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/my-health", label: "My Health", icon: HeartPulse },
  { to: "/insights", label: "Health Insights", icon: Sparkles },
  { to: "/causal-pathways", label: "Causal Pathways", icon: GitBranch },
  { to: "/simulator", label: "What-If Simulator", icon: FlaskConical },
  { to: "/alerts", label: "Health Alerts", icon: Bell },
  { to: "/relay-guide", label: "Relay Guide", icon: MessageCircle },
  { to: "/reports", label: "Wellness Reports", icon: FileText },
  { to: "/library", label: "Health Library", icon: BookOpen },
  { to: "/trust", label: "Trust Center", icon: ShieldCheck },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function Sidebar() {
  const loc = useLocation();
  const { user, logout } = useAuth();
  const { unreadCount } = useNotifications();

  const displayName = user?.name || "User";
  const initial = displayName.charAt(0).toUpperCase();
  const provider = user?.provider || "email";
  const providerLabel = provider === "google" ? "Google" : provider === "twitter" ? "Twitter" : "Email";

  return (
    <aside className="w-[260px] shrink-0 h-screen sticky top-0 p-4">
      <div className="soft-card h-full flex flex-col p-4">
        {/* Logo */}
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-11 h-11 rounded-2xl gradient-sage grid place-items-center text-white shadow-md">
            <HeartPulse className="w-5 h-5" />
          </div>
          <div>
            <div className="font-display text-lg font-semibold leading-tight">Relay-med</div>
            <div className="text-[11px] text-muted-foreground">Your AI Health Companion</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="mt-5 flex-1 space-y-1 overflow-y-auto">
          {nav.map((item) => {
            const active = loc.pathname === item.to;
            const Icon = item.icon;
            const badge = item.label === "Health Alerts" ? unreadCount : 0;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium shadow-sm"
                    : "text-muted-foreground hover:bg-mint/60 hover:text-foreground"
                }`}
              >
                <Icon className="w-[18px] h-[18px]" />
                <span className="flex-1">{item.label}</span>
                {badge > 0 && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full" style={{ color: "var(--coral)", background: "color-mix(in oklab, var(--coral) 18%, transparent)" }}>
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Upgrade card */}
        <div className="mt-4 rounded-2xl p-4 bg-mint/70 border border-[color:color-mix(in_oklab,var(--sage)_15%,transparent)]">
          <div className="flex items-center gap-2 text-sage font-medium text-sm">
            <Gem className="w-4 h-4" /> Upgrade to Pro
          </div>
          <p className="text-[11px] text-muted-foreground mt-1 leading-snug">
            Unlock advanced AI insights, longer forecasts & personalized recommendations.
          </p>
          <button className="mt-3 w-full neu-btn rounded-xl py-2 text-xs font-semibold text-sage hover:scale-[1.02] transition-transform">
            Upgrade Now
          </button>
        </div>

        {/* Profile */}
        <div className="mt-3 flex items-center gap-3 p-2 rounded-2xl hover:bg-mint/40 cursor-pointer group">
          <div className="relative">
            <div className="w-10 h-10 rounded-full gradient-sage grid place-items-center text-white font-semibold">{initial}</div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[var(--success)] ring-2 ring-white" />
          </div>
          <div className="flex-1">
            <div className="text-sm font-medium">{displayName}</div>
            <div className="text-[11px] text-muted-foreground">via {providerLabel}</div>
          </div>
          <button onClick={logout} className="opacity-0 group-hover:opacity-100 transition-opacity" title="Sign Out">
            <LogOut className="w-4 h-4 text-muted-foreground hover:text-foreground" />
          </button>
        </div>
      </div>
    </aside>
  );
}
