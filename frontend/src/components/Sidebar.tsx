"use client";

import React, { useState, useEffect } from "react";
import { LayoutDashboard, Library, User, Zap, History, Edit2, Check, X, Search } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { api } from "@/lib/api";
import { Session } from "./Dashboard";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SidebarItemProps {
    icon: React.ReactNode;
    label: string;
    active?: boolean;
    onClick?: () => void;
}

const SidebarItem = ({ icon, label, active, onClick }: SidebarItemProps) => (
    <div
        onClick={onClick}
        className={cn(
            "sidebar-item",
            active && "active"
        )}
    >
        {icon}
        <span className="tracking-wide">{label}</span>
        {active && (
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-white shadow-[0_0_15px_rgba(255,255,255,0.3)]" />
        )}
    </div>
);

interface SidebarProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
    sessions: Session[];
    activeSessionId: string | null;
    onSelectSession: (id: string) => void;
    onRefreshSessions: () => void;
}

export const Sidebar = ({ activeTab, onTabChange, sessions, activeSessionId, onSelectSession, onRefreshSessions }: SidebarProps) => {
    const [backendOnline, setBackendOnline] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editValue, setEditValue] = useState("");
    const [searchQuery, setSearchQuery] = useState("");

    const filteredSessions = sessions.filter(s =>
        s.uuid.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (s.label && s.label.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const handleSaveLabel = async (id: string) => {
        if (!editValue.trim()) {
            setEditingId(null);
            return;
        }
        try {
            await api.updateSessionLabel(id, editValue.trim());
            onRefreshSessions();
        } catch {
            // silent fail for now, maybe add toast later
        }
        setEditingId(null);
    };

    useEffect(() => {
        const check = async () => {
            try {
                const status = await api.getStatus();
                setBackendOnline(status.gpu_label !== "Offline");
            } catch {
                setBackendOnline(false);
            }
        };
        check();
        const interval = setInterval(check, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <aside className="w-72 h-screen border-r border-white/10 bg-black flex flex-col p-4 sticky top-0 z-50">
            {/* Logo */}
            <div className="mb-6 px-2 flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/[0.03] flex items-center justify-center border border-white/10 overflow-hidden">
                    <img src="/logo.png" alt="GI Scribe" className="w-7 h-7 object-contain grayscale invert brightness-200" />
                </div>
                <div>
                    <h1 className="text-lg font-black text-white tracking-tighter leading-none">
                        GI <span className="text-white/70">Scribe</span>
                    </h1>
                    <p className="text-[8px] font-bold text-white/30 uppercase tracking-[0.2em] mt-1">Enterprise Edition</p>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex flex-col gap-1.5 mb-4">
                <SidebarItem icon={<LayoutDashboard size={18} />} label="Clinical Desk" active={activeTab === "dashboard"} onClick={() => onTabChange("dashboard")} />
                <SidebarItem icon={<Library size={18} />} label="Medical Library" active={activeTab === "library"} onClick={() => onTabChange("library")} />
                <SidebarItem icon={<User size={18} />} label="Physician Profile" active={activeTab === "profile"} onClick={() => onTabChange("profile")} />
            </nav>

            {/* Sessions list */}
            <div className="flex-1 flex flex-col min-h-0 border-t border-white/[0.06] pt-3">
                <div className="flex items-center justify-between px-2 mb-2">
                    <h3 className="text-[10px] font-bold text-white/50 uppercase tracking-wider flex items-center gap-1.5">
                        <History size={12} />
                        Old Sessions
                    </h3>
                    <button onClick={onRefreshSessions} className="text-[9px] text-white/30 hover:text-white/60 transition-colors uppercase tracking-wider">Refresh</button>
                </div>
                <div className="px-2 mb-3">
                    <div className="relative">
                        <Search size={10} className="absolute left-2 top-1/2 -translate-y-1/2 text-white/30" />
                        <input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Find patient or session..."
                            className="w-full bg-white/[0.04] border border-white/10 rounded-md py-1.5 pl-6 pr-2 text-[10px] text-white focus:outline-none focus:border-white/30 placeholder-white/30"
                        />
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-1 pr-1">
                    {filteredSessions.length > 0 ? filteredSessions.map((s) => (
                        <div
                            key={s.uuid}
                            onClick={() => { if (editingId !== s.uuid) onSelectSession(s.uuid); }}
                            onDoubleClick={() => { setEditingId(s.uuid); setEditValue(s.label || ""); }}
                            className={`group px-3 py-2 rounded-lg cursor-pointer transition-all ${activeSessionId === s.uuid
                                ? "bg-white/[0.08] border border-white/15"
                                : "hover:bg-white/[0.03] border border-transparent"
                                }`}
                        >
                            {editingId === s.uuid ? (
                                <div className="flex items-center gap-1">
                                    <input
                                        autoFocus
                                        value={editValue}
                                        onChange={e => setEditValue(e.target.value)}
                                        onKeyDown={e => {
                                            if (e.key === "Enter") handleSaveLabel(s.uuid);
                                            if (e.key === "Escape") setEditingId(null);
                                        }}
                                        onClick={e => e.stopPropagation()}
                                        className="flex-1 bg-black/50 text-white text-[11px] px-1.5 py-0.5 rounded border border-white/20 focus:outline-none focus:border-white/40"
                                        placeholder="Enter label..."
                                    />
                                    <button onClick={(e) => { e.stopPropagation(); handleSaveLabel(s.uuid); }} className="p-0.5 text-emerald-400 hover:bg-emerald-400/20 rounded"><Check size={10} /></button>
                                    <button onClick={(e) => { e.stopPropagation(); setEditingId(null); }} className="p-0.5 text-white/40 hover:text-white/80 hover:bg-white/10 rounded"><X size={10} /></button>
                                </div>
                            ) : (
                                <div className="flex justify-between items-center group/item">
                                    <p className="text-[11px] font-semibold text-white truncate max-w-[120px]" title={s.label || s.uuid}>
                                        {s.label || (s.uuid.startsWith("GAS") ? s.uuid : s.uuid.slice(0, 8))}
                                    </p>
                                    <div className="flex items-center gap-1.5">
                                        <button 
                                            onClick={(e) => { e.stopPropagation(); setEditingId(s.uuid); setEditValue(s.label || ""); }}
                                            className="opacity-0 group-hover/item:opacity-100 p-0.5 text-white/30 hover:text-white/80 transition-opacity"
                                        >
                                            <Edit2 size={10} />
                                        </button>
                                        <span className="text-[9px] text-white/20 shrink-0">
                                            {new Date(s.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    )) : (
                        <div className="flex flex-col items-center text-white/15 py-6">
                            <History size={18} className="mb-1.5" />
                            <p className="text-[9px] uppercase tracking-widest">No sessions</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Engine Status */}
            <div className="pt-3 border-t border-white/[0.06] mt-2">
                <div className="flex items-center gap-1.5 mb-2.5">
                    <Zap size={11} className="text-white/40" />
                    <span className="text-[9px] font-bold text-white/40 uppercase tracking-wider">Engine</span>
                </div>
                <div className="flex gap-3">
                    <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${backendOnline ? "bg-emerald-500" : "bg-red-500"}`} />
                        <span className="text-[9px] text-white/40">Whisper</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${backendOnline ? "bg-emerald-500" : "bg-red-500"}`} />
                        <span className="text-[9px] text-white/40">Llama</span>
                    </div>
                </div>
            </div>

            {/* User */}
            <div className="flex items-center gap-3 pt-3 mt-3 border-t border-white/[0.06]">
                <div className="relative">
                    <div className="w-8 h-8 rounded-full bg-white/[0.05] border border-white/15" />
                    <div className={`absolute bottom-0 right-0 w-2.5 h-2.5 border-2 border-black rounded-full ${backendOnline ? "bg-emerald-500" : "bg-red-500"}`} />
                </div>
                <div>
                    <p className="text-xs font-bold text-white leading-none">Dr. Sasidhar</p>
                    <p className="text-[8px] text-white/30 mt-1 uppercase tracking-widest">Chief Gastro</p>
                </div>
            </div>
        </aside>
    );
};
