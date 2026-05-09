import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";

export interface Notification {
  id: string;
  severity: "high" | "medium" | "low";
  title: string;
  body: string;
  time: string;
  read: boolean;
  dismissed: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  markRead: (id: string) => void;
  dismiss: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

const STORAGE_KEY = "relaymed_notifications";

const DEFAULT_NOTIFICATIONS: Notification[] = [
  {
    id: "n1",
    severity: "high",
    title: "Elevated stress trend (3 days)",
    body: "Your stress indicators have been elevated for 3 consecutive days. Consider a mindfulness session or light exercise.",
    time: "2h ago",
    read: false,
    dismissed: false,
  },
  {
    id: "n2",
    severity: "medium",
    title: "Hydration below target",
    body: "Average intake 1.4L vs goal 2.2L this week. Try setting hourly water reminders.",
    time: "Yesterday",
    read: false,
    dismissed: false,
  },
  {
    id: "n3",
    severity: "low",
    title: "Resting HR returned to baseline",
    body: "Recovery validated against wearable + manual entries. Great progress!",
    time: "2 days ago",
    read: false,
    dismissed: false,
  },
  {
    id: "n4",
    severity: "medium",
    title: "Weekly wellness report ready",
    body: "Your weekly health summary is available in the Reports section.",
    time: "3 days ago",
    read: true,
    dismissed: false,
  },
  {
    id: "n5",
    severity: "low",
    title: "Sleep consistency improved",
    body: "Your bedtime variance decreased from 1.5h to 0.5h this week.",
    time: "4 days ago",
    read: true,
    dismissed: false,
  },
];

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setNotifications(JSON.parse(stored));
      } else {
        setNotifications(DEFAULT_NOTIFICATIONS);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_NOTIFICATIONS));
      }
    } catch {
      setNotifications(DEFAULT_NOTIFICATIONS);
    }
  }, []);

  const save = (updated: Notification[]) => {
    setNotifications(updated);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  };

  const markRead = useCallback((id: string) => {
    setNotifications((prev) => {
      const updated = prev.map((n) => (n.id === id ? { ...n, read: true } : n));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const dismiss = useCallback((id: string) => {
    setNotifications((prev) => {
      const updated = prev.map((n) => (n.id === id ? { ...n, dismissed: true } : n));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const clearAll = useCallback(() => {
    setNotifications((prev) => {
      const updated = prev.map((n) => ({ ...n, read: true }));
      localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      return updated;
    });
  }, []);

  const unreadCount = notifications.filter((n) => !n.read && !n.dismissed).length;

  return (
    <NotificationContext.Provider value={{ notifications, unreadCount, markRead, dismiss, clearAll }}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within <NotificationProvider>");
  return ctx;
}
