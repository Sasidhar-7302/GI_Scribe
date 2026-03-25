"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, Copy, Sparkles, History, LayoutDashboard, AlertCircle, CheckCircle2, Brain, ThumbsUp, Upload, Square, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";

export interface Session {
    uuid: string;
    transcript: string;
    summary: string;
    created_at: string;
    audio_path?: string;
    metadata?: Record<string, unknown>;
}

interface DashboardProps {
    initialSessionId?: string | null;
    onSessionLoaded?: () => void;
}

export const Dashboard = ({ initialSessionId, onSessionLoaded }: DashboardProps) => {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [summary, setSummary] = useState("");
    const [status, setStatus] = useState("Ready");
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [sessions, setSessions] = useState<Session[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [isSummarizing, setIsSummarizing] = useState(false);
    const [recordingSeconds, setRecordingSeconds] = useState(0);
    const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([]);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [feedbackCount, setFeedbackCount] = useState(0);
    const wsRef = useRef<WebSocket | null>(null);

    interface WSMessage {
        type: "transcript" | "summary" | "error";
        text?: string;
        uuid?: string;
        detail?: string;
    }

    useEffect(() => {
        navigator.mediaDevices?.enumerateDevices?.().then((devices) => {
            setMicDevices(devices.filter(d => d.kind === "audioinput"));
        }).catch(() => { });
    }, []);

    useEffect(() => {
        api.getPreferences().then(data => setFeedbackCount(data.feedback_count || 0)).catch(() => { });
    }, []);

    useEffect(() => {
        if (initialSessionId) {
            handleLoadSession(initialSessionId);
            onSessionLoaded?.();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [initialSessionId]);

    useEffect(() => {
        loadSessions();
        wsRef.current = api.connectWS((rawData: unknown) => {
            const data = rawData as WSMessage;
            if (data.type === "transcript" && data.text) {
                setTranscript(data.text);
                setStatus("Transcribing");
            } else if (data.type === "summary" && data.text && data.uuid) {
                setSummary(data.text);
                setStatus("Complete");
                setActiveSessionId(data.uuid);
                loadSessions();
            } else if (data.type === "error" && data.detail) {
                setError(data.detail);
            }
        });
        return () => { wsRef.current?.close(); };
    }, []);

    const loadSessions = async () => {
        try {
            const data = await api.listSessions();
            setSessions(data);
        } catch {
            console.error("Failed to load sessions");
        }
    };

    const handleLoadSession = async (id: string) => {
        try {
            const data = await api.getSession(id);
            setTranscript(data.transcript);
            setSummary(data.summary);
            setActiveSessionId(id);
            setAudioUrl(data.audio_path ? api.getAudioUrl(id) : null);
            setStatus("Session loaded");
        } catch {
            setError("Failed to load session.");
        }
    };

    const handleSummarize = async () => {
        if (!activeSessionId) return;
        try {
            setIsSummarizing(true);
            setStatus("Summarizing...");
            const data = await api.summarizeSession(activeSessionId);
            setSummary(data.summary);
            setSuccess("Summary regenerated.");
            setTimeout(() => setSuccess(null), 3000);
            setStatus("Complete");
        } catch {
            setError("Summarization failed.");
        } finally {
            setIsSummarizing(false);
        }
    };

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setSuccess("Copied.");
        setTimeout(() => setSuccess(null), 2000);
    };

    const handleIngestGas = async () => {
        try {
            setStatus("Ingesting...");
            await api.ingestGas();
            await loadSessions();
            setSuccess("Benchmarks ingested.");
            setTimeout(() => setSuccess(null), 3000);
            setStatus("Ready");
        } catch {
            setError("Ingestion failed.");
        }
    };

    const handleLoadAudio = () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "audio/*";
        input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (file) {
                setAudioUrl(URL.createObjectURL(file));
                setStatus("Audio loaded");
                setSuccess(`Loaded: ${file.name}`);
                setTimeout(() => setSuccess(null), 3000);
            }
        };
        input.click();
    };

    const formatTimer = (totalSeconds: number) => {
        const m = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
        const s = String(totalSeconds % 60).padStart(2, "0");
        return `${m}:${s}`;
    };

    const handleToggleRecording = async () => {
        try {
            setError(null);
            if (!isRecording) {
                const res = await api.startRecording();
                setIsRecording(true);
                setStatus("Recording");
                setTranscript("");
                setSummary("");
                setActiveSessionId(res.uuid);
                setRecordingSeconds(0);
                timerRef.current = setInterval(() => setRecordingSeconds(s => s + 1), 1000);
            } else {
                if (activeSessionId) await api.stopRecording(activeSessionId);
                setIsRecording(false);
                setStatus("Processing...");
                if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
            }
        } catch {
            setError("Failed to communicate with AI engine.");
        }
    };

    const handleApproveAndLearn = async () => {
        if (!activeSessionId) return;
        try {
            setError(null);
            await api.updateSession(activeSessionId, { summary, transcript });
            await api.approveSession(activeSessionId);
            await loadSessions();
            const prefs = await api.getPreferences();
            setFeedbackCount(prefs.feedback_count || 0);
            setSuccess("Approved — learning from your style");
            setTimeout(() => setSuccess(null), 3000);
        } catch {
            setError("Failed to save — is the backend running?");
        }
    };

    return (
        <main className="flex-1 overflow-y-auto bg-black custom-scrollbar" suppressHydrationWarning>
            <div className="max-w-[1800px] mx-auto px-6 py-6 flex flex-col gap-5">

                {/* ── Compact Header ──────────────────────────────── */}
                <header className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-white tracking-tight">Clinical Workspace</h2>
                        <p className="text-xs text-white/40 mt-1">AI transcription & synthesis for gastroenterology</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleIngestGas}
                            className="px-4 py-2 rounded-lg bg-white/[0.04] border border-white/10 hover:border-white/25 text-white/60 hover:text-white text-[10px] font-semibold uppercase tracking-wider transition-all"
                        >
                            Import Benchmarks
                        </button>
                        <div className="px-3 py-2 rounded-lg border border-white/10 text-white/40 text-[10px] font-semibold uppercase tracking-wider">HIPAA</div>
                    </div>
                </header>

                {/* ── Toast Alerts ────────────────────────────────── */}
                <AnimatePresence mode="wait">
                    {error && (
                        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                            className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-3 text-sm"
                        >
                            <AlertCircle size={16} />
                            <span className="flex-1">{error}</span>
                            <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100 text-xs">✕</button>
                        </motion.div>
                    )}
                    {success && (
                        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                            className="px-4 py-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-3 text-sm"
                        >
                            <CheckCircle2 size={16} />
                            <span className="flex-1">{success}</span>
                            <button onClick={() => setSuccess(null)} className="opacity-50 hover:opacity-100 text-xs">✕</button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* ── Recording Control Bar ───────────────────────── */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.02] border border-white/[0.06]">
                    <button
                        onClick={handleToggleRecording}
                        className={`flex items-center gap-2.5 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all ${isRecording
                            ? "bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                            : "bg-white text-black hover:bg-white/90"
                            }`}
                    >
                        {isRecording ? (
                            <>
                                <Square size={14} className="fill-current" />
                                Stop
                            </>
                        ) : (
                            <>
                                <Mic size={14} />
                                Record
                            </>
                        )}
                    </button>

                    {/* Timer */}
                    <div className={`font-mono text-sm tabular-nums tracking-wider px-3 py-1.5 rounded-lg ${isRecording ? "text-red-400 bg-red-500/10" : "text-white/30 bg-white/[0.02]"}`}>
                        {formatTimer(isRecording ? recordingSeconds : 0)}
                    </div>

                    {/* Status */}
                    <span className="text-[11px] text-white/40 font-medium">{status}</span>

                    {/* Spacer */}
                    <div className="flex-1" />

                    {/* Mic selector */}
                    <div className="relative">
                        <select className="appearance-none bg-white/[0.04] border border-white/10 rounded-lg pl-3 pr-7 py-2 text-[11px] text-white/60 focus:outline-none focus:border-white/30 cursor-pointer">
                            {micDevices.length > 0 ? micDevices.map((d, i) => (
                                <option key={d.deviceId || i} value={d.deviceId}>{d.label || `Mic ${i + 1}`}</option>
                            )) : (
                                <option>Default Mic</option>
                            )}
                        </select>
                        <ChevronDown size={12} className="absolute right-2 top-1/2 -translate-y-1/2 text-white/30 pointer-events-none" />
                    </div>

                    {/* Load audio file */}
                    <button
                        onClick={handleLoadAudio}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.04] border border-white/10 hover:border-white/25 text-white/60 hover:text-white text-[11px] font-medium transition-all"
                    >
                        <Upload size={13} />
                        Load Audio
                    </button>
                </div>

                {/* Audio player */}
                {audioUrl && (
                    <div className="px-4 py-2 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center">
                        <audio controls src={audioUrl} className="w-full h-8 opacity-70 hover:opacity-100 transition-opacity" style={{ filter: "invert(1) grayscale(1)" }} />
                    </div>
                )}

                {/* ── Main Work Area ─────────────────────────────── */}
                <div className="grid grid-cols-12 gap-5 flex-1 min-h-0">

                    {/* Session Archive — Left Panel */}
                    <div className="col-span-12 lg:col-span-3 flex flex-col">
                        <section className="glass-panel flex flex-col overflow-hidden flex-1">
                            <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                                    <History size={14} />
                                    Sessions
                                </h3>
                                <button onClick={loadSessions} className="text-[10px] text-white/40 hover:text-white transition-colors uppercase tracking-wider">Refresh</button>
                            </div>
                            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
                                {sessions.length > 0 ? sessions.map((s) => (
                                    <motion.div
                                        whileTap={{ scale: 0.98 }}
                                        key={s.uuid}
                                        onClick={() => handleLoadSession(s.uuid)}
                                        className={`p-3 rounded-xl border cursor-pointer transition-all ${activeSessionId === s.uuid
                                            ? "border-white/20 bg-white/[0.06]"
                                            : "border-transparent hover:bg-white/[0.03]"
                                            }`}
                                    >
                                        <div className="flex justify-between items-center mb-1.5">
                                            <p className="text-xs font-semibold text-white truncate max-w-[140px]" title={s.uuid}>
                                                {s.uuid.startsWith("GAS") ? s.uuid : s.uuid.slice(0, 8)}
                                            </p>
                                            <span className="text-[10px] text-white/30">
                                                {new Date(s.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <span className={`text-[9px] font-semibold uppercase tracking-wider ${s.uuid.startsWith("GAS") ? "text-amber-500/70" : "text-white/30"}`}>
                                            {s.uuid.startsWith("GAS") ? "benchmark" : "clinical"}
                                        </span>
                                    </motion.div>
                                )) : (
                                    <div className="flex flex-col items-center justify-center text-white/20 py-12">
                                        <History size={24} className="mb-2" />
                                        <p className="text-[10px] uppercase tracking-widest">No sessions</p>
                                    </div>
                                )}
                            </div>
                        </section>
                    </div>

                    {/* Transcript + Synthesis — Right Panels */}
                    <div className="col-span-12 lg:col-span-9 flex flex-col gap-5">

                        {/* Acoustic Stream */}
                        <section className="glass-panel flex flex-col flex-1 min-h-[280px] overflow-hidden">
                            <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                                    <Mic size={14} className={isRecording ? "text-red-400 animate-pulse" : ""} />
                                    Transcript
                                    {isRecording && <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />}
                                </h3>
                                <button onClick={() => handleCopy(transcript)} className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white/60 transition-all" title="Copy">
                                    <Copy size={14} />
                                </button>
                            </div>
                            <div className="flex-1 relative">
                                <textarea
                                    value={transcript}
                                    onChange={(e) => setTranscript(e.target.value)}
                                    placeholder="Transcription will appear here..."
                                    className="absolute inset-0 p-5 text-sm text-white/80 leading-relaxed bg-transparent resize-none focus:outline-none placeholder-white/15 custom-scrollbar"
                                />
                            </div>
                        </section>

                        {/* Clinical Synthesis */}
                        <section className="glass-panel flex flex-col flex-1 min-h-[320px] overflow-hidden">
                            <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
                                <h3 className="text-[11px] font-bold text-white/70 uppercase tracking-wider flex items-center gap-2">
                                    <LayoutDashboard size={14} />
                                    Clinical Note
                                </h3>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={handleSummarize}
                                        disabled={!activeSessionId || isSummarizing}
                                        className={`p-2 rounded-lg transition-all ${isSummarizing ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/30 hover:text-white/60"}`}
                                        title="Regenerate"
                                    >
                                        <Sparkles size={14} className={isSummarizing ? "animate-spin" : ""} />
                                    </button>
                                    <button onClick={() => handleCopy(summary)} className="p-2 rounded-lg hover:bg-white/5 text-white/30 hover:text-white/60 transition-all" title="Copy">
                                        <Copy size={14} />
                                    </button>
                                    <div className="w-px h-5 bg-white/10 mx-1" />
                                    <button
                                        onClick={handleApproveAndLearn}
                                        disabled={!activeSessionId}
                                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[11px] font-semibold transition-all ${activeSessionId
                                            ? "bg-white text-black hover:bg-white/90"
                                            : "bg-white/5 text-white/20 cursor-not-allowed"
                                            }`}
                                    >
                                        <ThumbsUp size={12} />
                                        Approve & Learn
                                        {feedbackCount > 0 && (
                                            <span className="px-1.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-[9px] font-bold" title={`Adapted from ${feedbackCount} corrections`}>
                                                <Brain size={8} className="inline mr-0.5" />{feedbackCount}
                                            </span>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 relative">
                                {isSummarizing ? (
                                    <div className="absolute inset-0 p-5 flex flex-col gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-5 h-5 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                                            <p className="text-xs text-white/50">Generating clinical note...</p>
                                        </div>
                                        <motion.div animate={{ opacity: [0.05, 0.15, 0.05] }} transition={{ repeat: Infinity, duration: 2 }} className="h-3 w-3/4 bg-white/5 rounded" />
                                        <motion.div animate={{ opacity: [0.05, 0.15, 0.05] }} transition={{ repeat: Infinity, duration: 2, delay: 0.3 }} className="h-3 w-full bg-white/5 rounded" />
                                        <motion.div animate={{ opacity: [0.05, 0.15, 0.05] }} transition={{ repeat: Infinity, duration: 2, delay: 0.6 }} className="h-3 w-1/2 bg-white/5 rounded" />
                                    </div>
                                ) : (
                                    <textarea
                                        value={summary}
                                        onChange={(e) => setSummary(e.target.value)}
                                        placeholder="Clinical note will appear here..."
                                        className="absolute inset-0 p-5 text-sm text-white/80 leading-relaxed bg-transparent resize-none focus:outline-none placeholder-white/15 custom-scrollbar"
                                    />
                                )}
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </main>
    );
};
