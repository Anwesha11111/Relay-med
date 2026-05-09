import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/PageShell";
import { Bell, AlertTriangle, Info, CheckCircle2, Check, X, Filter } from "lucide-react";
import { useNotifications, Notification } from "@/hooks/useNotifications";
import { useState } from "react";

export const Route = createFileRoute("/alerts")({ component: Page });

const sevIcons: Record<string, typeof AlertTriangle> = {
  high: AlertTriangle,
  medium: Info,
  low: CheckCircle2,
};

const sevColors: Record<string, string> = {
  high: "bg-[color:color-mix(in_oklab,var(--coral)_15%,white)] text-[color:var(--coral)]",
  medium: "bg-[color:color-mix(in_oklab,var(--warning)_22%,white)] text-[color:color-mix(in_oklab,var(--warning)_60%,black)]",
  low: "bg-mint text-sage",
};

function Page() {
  const { notifications, markRead, dismiss, clearAll, unreadCount } = useNotifications();
  const [filter, setFilter] = useState<"all" | "unread">("all");

  const visible = notifications.filter((n) => !n.dismissed);
  const filtered = filter === "unread" ? visible.filter((n) => !n.read) : visible;

  return (
    <PageShell title="Health Alerts" subtitle="Prioritized notifications based on temporal risk trajectories." icon={Bell}>
      {/* Controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter("all")}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${filter === "all" ? "bg-sage text-white" : "bg-white border hover:bg-gray-50"}`}
          >
            All ({visible.length})
          </button>
          <button
            onClick={() => setFilter("unread")}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${filter === "unread" ? "bg-sage text-white" : "bg-white border hover:bg-gray-50"}`}
          >
            Unread ({unreadCount})
          </button>
        </div>
        <button onClick={clearAll} className="text-xs text-sage hover:underline flex items-center gap-1">
          <Check className="w-3 h-3" /> Mark all as read
        </button>
      </div>

      {/* Alert list */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <div className="soft-card p-8 text-center">
            <CheckCircle2 className="w-10 h-10 text-sage mx-auto mb-3 opacity-50" />
            <div className="text-sm font-medium text-muted-foreground">
              {filter === "unread" ? "No unread notifications" : "No notifications"}
            </div>
          </div>
        ) : (
          filtered.map((n) => {
            const Icon = sevIcons[n.severity] || Info;
            return (
              <div
                key={n.id}
                className={`rounded-2xl border bg-white p-4 flex items-start gap-3 hover:shadow-md transition-all ${
                  n.read ? "opacity-60" : ""
                }`}
              >
                <div className={`w-10 h-10 rounded-xl grid place-items-center shrink-0 ${sevColors[n.severity]}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-medium text-sm">{n.title}</div>
                    <div className="text-[11px] text-muted-foreground shrink-0">{n.time}</div>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{n.body}</p>
                  <div className="flex items-center gap-3 mt-2">
                    {!n.read && (
                      <button
                        onClick={() => markRead(n.id)}
                        className="text-xs text-sage flex items-center gap-1 hover:underline"
                      >
                        <Check className="w-3.5 h-3.5" /> Mark as read
                      </button>
                    )}
                    <button
                      onClick={() => dismiss(n.id)}
                      className="text-xs text-muted-foreground flex items-center gap-1 hover:underline"
                    >
                      <X className="w-3.5 h-3.5" /> Dismiss
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </PageShell>
  );
}
