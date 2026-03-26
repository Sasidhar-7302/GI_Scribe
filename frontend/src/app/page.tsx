"use client";

import { useState, useCallback } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Dashboard, Session } from "@/components/Dashboard";
import { LibraryView } from "@/components/LibraryView";
import { ProfileView } from "@/components/ProfileView";

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [pendingSessionId, setPendingSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    setActiveTab("dashboard");
  }, []);

  const handleRefreshSessions = useCallback(() => {
    // Trigger refresh via the window global set by Dashboard
    const fn = (window as unknown as { __refreshSessions?: () => void }).__refreshSessions;
    if (typeof fn === "function") fn();
  }, []);

  return (
    <div className="flex h-screen bg-black overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onRefreshSessions={handleRefreshSessions}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {activeTab === "dashboard" && (
          <Dashboard
            initialSessionId={pendingSessionId}
            onSessionLoaded={() => setPendingSessionId(null)}
            onSessionsChange={setSessions}
            activeSessionId={activeSessionId}
            onActiveSessionChange={setActiveSessionId}
          />
        )}
        {activeTab === "library" && <LibraryView onSelectSession={handleSelectSession} />}
        {activeTab === "profile" && <ProfileView />}
      </div>
    </div>
  );
}
