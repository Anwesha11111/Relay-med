import { Link } from "@tanstack/react-router";
import { Sidebar } from "./Sidebar";
import { Bell, Monitor, ChevronDown, X, Check, RefreshCw } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useNotifications } from "@/hooks/useNotifications";
import { useState } from "react";

function SyncModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="soft-card p-6 w-full max-w-md fade-in" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-lg font-semibold">Sync Devices</h3>
          <button onClick={onClose} className="w-8 h-8 grid place-items-center rounded-lg hover:bg-gray-100"><X className="w-4 h-4" /></button>
        </div>
        <p className="text-sm text-muted-foreground mb-4">
          Your data syncs automatically across all devices signed into the same account.
        </p>
        <div className="space-y-3">
          {[
            { name: "This Device", type: "Desktop — Chrome", synced: true },
            { name: "Shreya's Phone", type: "Mobile — Relay-med App", synced: true },
            { name: "Tablet", type: "iPad — Safari", synced: false },
          ].map((d) => (
            <div key={d.name} className="flex items-center justify-between rounded-xl border p-3">
              <div>
                <div className="text-sm font-medium">{d.name}</div>
                <div className="text-[10px] text-muted-foreground">{d.type}</div>
              </div>
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${d.synced ? "bg-mint text-sage" : "bg-gray-100 text-gray-500"}`}>
                {d.synced ? "Synced" : "Not synced"}
              </span>
            </div>
          ))}
        </div>
        <button onClick={() => { alert("All devices successfully synced!"); onClose(); }} className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl gradient-sage text-white text-sm font-medium hover:opacity-90 transition-opacity">
          <RefreshCw className="w-4 h-4" /> Sync All Now
        </button>
        <p className="text-[10px] text-muted-foreground text-center mt-3">
          Same account = same data. Sign in on another device to see your health data there too.
        </p>
      </div>
    </div>
  );
}

function NotificationDropdown({ onClose }: { onClose: () => void }) {
  const { notifications, markRead, dismiss, clearAll } = useNotifications();
  const visible = notifications.filter((n) => !n.dismissed);

  const sevColors: Record<string, string> = {
    high: "bg-[color:color-mix(in_oklab,var(--coral)_15%,white)] text-[color:var(--coral)]",
    medium: "bg-[color:color-mix(in_oklab,var(--warning)_22%,white)] text-[color:color-mix(in_oklab,var(--warning)_60%,black)]",
    low: "bg-mint text-sage",
  };

  return (
    <div className="fixed inset-0 z-40" onClick={onClose}>
      <div className="absolute right-6 top-16 w-96 soft-card p-4 fade-in shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-display font-semibold text-sm">Notifications</h3>
          <button onClick={clearAll} className="text-[10px] text-sage hover:underline">Mark all read</button>
        </div>
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {visible.length === 0 ? (
            <div className="text-sm text-muted-foreground text-center py-6">No notifications</div>
          ) : (
            visible.map((n) => (
              <div key={n.id} className={`rounded-xl border p-3 flex items-start gap-3 transition-colors ${n.read ? "opacity-60" : ""}`}>
                <div className={`w-8 h-8 rounded-lg grid place-items-center shrink-0 ${sevColors[n.severity]}`}>
                  <Bell className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs font-medium truncate">{n.title}</div>
                    <div className="text-[9px] text-muted-foreground shrink-0">{n.time}</div>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">{n.body}</p>
                  <div className="flex gap-2 mt-1.5">
                    {!n.read && (
                      <button onClick={() => markRead(n.id)} className="text-[10px] text-sage flex items-center gap-0.5 hover:underline">
                        <Check className="w-3 h-3" /> Read
                      </button>
                    )}
                    <button onClick={() => dismiss(n.id)} className="text-[10px] text-muted-foreground flex items-center gap-0.5 hover:underline">
                      <X className="w-3 h-3" /> Dismiss
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export function AppLayout({
  greeting,
  subtitle,
  children,
}: {
  greeting: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const { unreadCount } = useNotifications();
  const [showSync, setShowSync] = useState(false);
  const [showNotifs, setShowNotifs] = useState(false);

  const displayName = user?.name || "there";
  const initial = displayName.charAt(0).toUpperCase();

  // Dynamic greeting based on time
  const hour = new Date().getHours();
  const timeGreeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0 px-6 pb-10">
        <header className="flex items-center justify-between pt-6 pb-6 fade-in">
          <div>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">
              {timeGreeting}, {displayName} <span className="inline-block animate-float">🌿</span>
            </h1>
            <p className="text-sm text-muted-foreground mt-1">{subtitle}</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSync(true)}
              className="neu-btn flex items-center gap-2 text-sm px-4 py-2.5 rounded-2xl"
            >
              <Monitor className="w-4 h-4" /> Sync Devices
            </button>
            <button
              onClick={() => setShowNotifs(!showNotifs)}
              className="relative neu-btn w-11 h-11 grid place-items-center rounded-2xl"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <span
                  className="absolute -top-1 -right-1 w-5 h-5 text-[10px] font-bold rounded-full grid place-items-center text-white"
                  style={{ background: "var(--coral)" }}
                >
                  {unreadCount}
                </span>
              )}
            </button>
            <Link to="/settings" className="neu-btn flex items-center gap-2 pl-1 pr-3 py-1 rounded-2xl">
              <div className="w-8 h-8 rounded-full gradient-sage grid place-items-center text-white text-xs font-semibold">
                {initial}
              </div>
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </Link>
          </div>
        </header>
        {children}
      </main>
      {showSync && <SyncModal onClose={() => setShowSync(false)} />}
      {showNotifs && <NotificationDropdown onClose={() => setShowNotifs(false)} />}
    </div>
  );
}
