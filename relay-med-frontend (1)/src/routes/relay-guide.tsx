import { createFileRoute } from "@tanstack/react-router";
import { AppLayout } from "@/components/AppLayout";
import { RelayGuidePanel } from "@/components/RelayGuidePanel";
import { SecurityFooter } from "@/components/SecurityFooter";
import { MessageCircle, Sparkles } from "lucide-react";

export const Route = createFileRoute("/relay-guide")({ component: Page });

function Page() {
  return (
    <AppLayout greeting="Relay Guide" subtitle="Talk to your calm, intelligent AI health companion.">
      <div className="max-w-4xl mx-auto w-full space-y-4">
        {/* Small conversation summary widget */}
        <div className="soft-card px-4 py-3 fade-in flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-mint grid place-items-center text-sage shrink-0">
            <MessageCircle className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Current Conversation</div>
            <div className="text-sm font-medium truncate">Weekly health check-in · 3 messages</div>
          </div>
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-sage bg-mint/60 px-2.5 py-1 rounded-full">
            <Sparkles className="w-3 h-3" /> Active
          </div>
        </div>

        {/* Main chat takes most of the space */}
        <div className="fade-in">
          <RelayGuidePanel />
        </div>
      </div>
      <SecurityFooter />
    </AppLayout>
  );
}
