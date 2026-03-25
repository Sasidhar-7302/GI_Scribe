"use client";

import React, { useState, useEffect } from "react";
import { Library, Search, FileText, Play } from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

import { Session } from "./Dashboard";

interface LibraryViewProps {
    onSelectSession?: (sessionId: string) => void;
}

export const LibraryView = ({ onSelectSession }: LibraryViewProps) => {
    const [sessions, setSessions] = useState<Session[]>([]);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        const load = async () => {
            const data = await api.listSessions();
            setSessions(data);
        };
        load();
    }, []);

    const filtered = sessions.filter(s =>
        s.uuid.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (typeof s.metadata?.disease === "string" && s.metadata.disease.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <main className="flex-1 overflow-y-auto bg-black custom-scrollbar">
            <div className="max-w-[1800px] mx-auto px-6 py-6 flex flex-col gap-5">
                <header>
                    <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
                        <Library size={22} className="text-white/60" />
                        Medical Library
                    </h2>
                    <p className="text-xs text-white/40 mt-1">Archive of clinical encounters and benchmarks</p>
                </header>

                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30" size={16} />
                    <input
                        type="text"
                        placeholder="Search sessions or conditions..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-11 pr-4 py-3 rounded-xl border border-white/[0.08] bg-white/[0.02] text-sm text-white placeholder-white/25 focus:outline-none focus:border-white/20 transition-all"
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                    {filtered.map(s => (
                        <motion.div
                            whileHover={{ y: -2 }}
                            key={s.uuid}
                            onClick={() => onSelectSession?.(s.uuid)}
                            className="glass-panel p-5 hover:border-white/15 transition-all cursor-pointer group"
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <h4 className="font-semibold text-white text-sm">{s.uuid}</h4>
                                    <p className="text-[10px] text-white/30 mt-1">
                                        {new Date(s.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                                <span className={`text-[9px] font-semibold uppercase tracking-wider px-2 py-1 rounded-md ${s.uuid.startsWith("GAS")
                                    ? "text-amber-500/70 bg-amber-500/10"
                                    : "text-white/40 bg-white/[0.04]"
                                    }`}>
                                    {s.uuid.startsWith("GAS") ? "Benchmark" : "Clinical"}
                                </span>
                            </div>
                            <p className="text-xs text-white/50 line-clamp-2 mb-4 leading-relaxed min-h-[2.5rem]">
                                {s.summary || <span className="italic text-white/20">No summary available</span>}
                            </p>
                            <div className="flex items-center justify-between pt-3 border-t border-white/[0.05]">
                                <div className="flex gap-3">
                                    <div className="flex items-center gap-1 text-white/25 group-hover:text-white/50 transition-colors">
                                        <FileText size={12} />
                                        <span className="text-[10px]">Report</span>
                                    </div>
                                    {s.audio_path && (
                                        <div className="flex items-center gap-1 text-white/25 group-hover:text-white/50 transition-colors">
                                            <Play size={12} />
                                            <span className="text-[10px]">Audio</span>
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={(e) => { e.stopPropagation(); onSelectSession?.(s.uuid); }}
                                    className="text-[10px] text-white/30 hover:text-white transition-colors"
                                >View →</button>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {filtered.length === 0 && (
                    <div className="flex flex-col items-center justify-center text-white/20 py-20">
                        <Library size={32} className="mb-3" />
                        <p className="text-xs">No sessions found</p>
                    </div>
                )}
            </div>
        </main>
    );
};
