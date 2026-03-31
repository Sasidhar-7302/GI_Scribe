"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, Copy, Sparkles, LayoutDashboard, AlertCircle, CheckCircle2, Brain, ThumbsUp, Upload, Square, ChevronDown, FileText, Send, Sun, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";

export interface Session {
    uuid: string;
    transcript: string;
    summary: string;
    label?: string;
    created_at: string;
    audio_path?: string;
    metadata?: Record<string, unknown>;
}

interface DashboardProps {
    initialSessionId?: string | null;
    onSessionLoaded?: () => void;
    onSessionsChange?: (sessions: Session[]) => void;
    activeSessionId: string | null;
    onActiveSessionChange: (id: string | null) => void;
}

export const Dashboard = ({ initialSessionId, onSessionLoaded, onSessionsChange, activeSessionId, onActiveSessionChange }: DashboardProps) => {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [summary, setSummary] = useState("");
    const [status, setStatus] = useState("Ready");
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [isSummarizing, setIsSummarizing] = useState(false);
    const [recordingSeconds, setRecordingSeconds] = useState(0);
    const [micDevices, setMicDevices] = useState<MediaDeviceInfo[]>([]);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [feedbackCount, setFeedbackCount] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [lightMode, setLightMode] = useState(false);
    const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const wsRef = useRef<WebSocket | null>(null);

    interface WSMessage {
        type: "transcript" | "summary" | "error" | "status";
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
        if (typeof document !== "undefined") {
            setLightMode(document.documentElement.classList.contains("theme-light"));
        }
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
            const data = rawData as WSMessage & { percentage?: number };
            if (data.type === "transcript") {
                if (data.text !== undefined) setTranscript(data.text);
                setStatus(data.percentage !== undefined ? `Transcribing... ${data.percentage}%` : "Transcribing...");
            } else if (data.type === "summary" && data.text && data.uuid) {
                setSummary(data.text);
                setStatus("Complete");
                onActiveSessionChange(data.uuid);
                setIsProcessing(false);
                setIsRecording(false);
                if (timerRef.current) {
                    clearInterval(timerRef.current);
                    timerRef.current = null;
                }
                loadSessions();
            } else if (data.type === "status" && data.text) {
                setStatus(data.text);
            } else if (data.type === "error" && data.detail) {
                setError(data.detail);
                setIsProcessing(false);
            }
        });
        return () => { wsRef.current?.close(); };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const loadSessions = async () => {
        try {
            const data = await api.listSessions();
            onSessionsChange?.(data);
        } catch {
            console.error("Failed to load sessions");
        }
    };

    // Expose loadSessions for external refresh & Keyboard binding
    useEffect(() => {
        if (typeof window !== "undefined") {
            (window as unknown as { __refreshSessions?: () => void }).__refreshSessions = loadSessions;
        }

        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'r') {
                e.preventDefault();
                handleToggleRecordingRef.current();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleLoadSession = async (id: string) => {
        try {
            const data = await api.getSession(id);
            setTranscript(data.transcript);
            setSummary(data.summary);
            onActiveSessionChange(id);
            setAudioUrl(data.audio_path ? api.getAudioUrl(id) : null);
            setStatus("Session loaded");
        } catch {
            setError("Failed to load session.");
        }
    };

    // When activeSessionId changes externally (sidebar click), load it
    const prevSessionRef = useRef<string | null>(null);
    const isNewSessionRef = useRef<boolean>(false);
    useEffect(() => {
        if (activeSessionId && activeSessionId !== prevSessionRef.current) {
            if (isNewSessionRef.current) {
                isNewSessionRef.current = false;
            } else {
                handleLoadSession(activeSessionId);
            }
        }
        prevSessionRef.current = activeSessionId;
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeSessionId]);

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

    const triggerAutoSave = (newTranscript: string, newSummary: string) => {
        if (!activeSessionId) return;
        if (autoSaveTimeoutRef.current) clearTimeout(autoSaveTimeoutRef.current);
        autoSaveTimeoutRef.current = setTimeout(async () => {
            try {
                await api.updateSession(activeSessionId, { transcript: newTranscript, summary: newSummary });
                const currentSessions = await api.listSessions();
                onSessionsChange?.(currentSessions);
            } catch {
                // Background fail
            }
        }, 1500);
    };

    const handleExportEHR = () => {
        const formatted = `CLINICAL NOTE\nDate: ${new Date().toLocaleDateString()}\nProvider: Dr. Sasidhar Y.\n\n${summary}`;
        navigator.clipboard.writeText(formatted);
        setSuccess("Copied to EHR format.");
        setTimeout(() => setSuccess(null), 3000);
    };

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setSuccess("Copied.");
        setTimeout(() => setSuccess(null), 2000);
    };



    const handleLoadAudio = () => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "audio/*";
        input.onchange = async (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (!file) return;
            try {
                setError(null);
                setAudioUrl(URL.createObjectURL(file));
                setIsProcessing(true);
                setStatus("Uploading...");
                setTranscript("");
                setSummary("");
                isNewSessionRef.current = true;
                const res = await api.uploadAudio(file);
                onActiveSessionChange(res.uuid);
                setStatus("Initializing AI...");
                setSuccess(`Processing: ${file.name}`);
                setTimeout(() => setSuccess(null), 3000);
            } catch {
                setError("Upload failed — is the backend running?");
                setIsProcessing(false);
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
                isNewSessionRef.current = true;
                const res = await api.startRecording();
                setIsRecording(true);
                setStatus("Recording...");
                setTranscript("");
                setSummary("");
                onActiveSessionChange(res.uuid);
                setRecordingSeconds(0);
                timerRef.current = setInterval(() => setRecordingSeconds(s => s + 1), 1000);
            } else {
                if (activeSessionId) await api.stopRecording(activeSessionId);
                setIsRecording(false);
                setStatus("Initializing AI...");
                setIsProcessing(true);
                if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
            }
        } catch {
            setError("Failed to communicate with AI engine.");
        }
    };

    const toggleTheme = () => {
        if (lightMode) {
            document.documentElement.classList.remove("theme-light");
            setLightMode(false);
        } else {
            document.documentElement.classList.add("theme-light");
            setLightMode(true);
        }
    };

    const handleToggleRecordingRef = useRef(handleToggleRecording);
    useEffect(() => {
        handleToggleRecordingRef.current = handleToggleRecording;
    }, [handleToggleRecording]);

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
        <main className="flex-1 flex flex-col h-screen overflow-hidden bg-black" suppressHydrationWarning>
            <div className="flex flex-col h-full px-5 py-4 gap-3">

                {/* Header row */}
                <div className="flex items-center justify-between shrink-0">
                    <div>
                        <h2 className="text-xl font-bold text-white tracking-tight">Clinical Workspace</h2>
                        <p className="text-[10px] text-white/30 mt-0.5">AI transcription & synthesis for gastroenterology</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button onClick={toggleTheme} className="p-1.5 rounded-lg bg-white/[0.04] border border-white/10 hover:border-white/25 text-white/50 hover:text-white transition-all" title="Toggle Light Mode">
                            {lightMode ? <Moon size={12} /> : <Sun size={12} />}
                        </button>
                        <div className="px-2.5 py-1.5 rounded-lg border border-white/10 text-white/30 text-[9px] font-semibold uppercase tracking-wider">HIPAA</div>
                    </div>
                </div>

                {/* Toasts */}
                <AnimatePresence mode="wait">
                    {error && (
                        <motion.div key="error-toast" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                            className="px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 flex items-center gap-2 text-xs shrink-0"
                        >
                            <AlertCircle size={14} />
                            <span className="flex-1">{error}</span>
                            <button onClick={() => setError(null)} className="opacity-50 hover:opacity-100 text-xs">✕</button>
                        </motion.div>
                    )}
                    {success && (
                        <motion.div key="success-toast" initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                            className="px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2 text-xs shrink-0"
                        >
                            <CheckCircle2 size={14} />
                            <span className="flex-1">{success}</span>
                            <button onClick={() => setSuccess(null)} className="opacity-50 hover:opacity-100 text-xs">✕</button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Dynamic Recording Controls & Main Content Area */}
                {(() => {
                    const isEmpty = !activeSessionId && !isRecording && !isProcessing && !transcript && !summary;
                    return (
                        <>
                            {/* Recording Controls (Animated between center and top) */}
                            <motion.div
                                layout
                                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                className={isEmpty 
                                    ? "flex-1 flex flex-col items-center justify-center mt-[-10vh]" 
                                    : "shrink-0"
                                }
                            >
                                {isEmpty && (
                                    <motion.div layout initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.8 }} className="relative flex items-center justify-center mb-10">
                                        <div className="absolute inset-0 bg-white/5 rounded-full animate-pulse-ring" />
                                        <div className="absolute inset-[-20px] bg-white/[0.02] rounded-full animate-pulse-ring" style={{ animationDelay: '1s' }} />
                                        <div className="w-32 h-32 rounded-full bg-white/5 border border-white/10 flex items-center justify-center z-10 shadow-[0_0_40px_rgba(255,255,255,0.05)]">
                                            <Mic size={48} className="text-white/40" />
                                        </div>
                                    </motion.div>
                                )}

                                <motion.div layout className={isEmpty 
                                    ? "flex flex-col items-center gap-4 p-8 rounded-3xl bg-white/[0.02] border border-white/[0.05] shadow-2xl backdrop-blur-3xl w-[400px]" 
                                    : "flex items-center gap-2.5 p-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] w-full"
                                }>
                                    <motion.button layout
                                        onClick={handleToggleRecording}
                                        className={`flex items-center justify-center gap-2 rounded-lg font-semibold transition-all ${isEmpty ? "w-full py-4 text-base" : "px-4 py-2 text-xs"} ${isRecording
                                            ? "bg-red-500 text-white shadow-[0_0_16px_rgba(239,68,68,0.3)]"
                                            : "bg-white text-black hover:bg-white/90 shadow-xl shadow-white/10"
                                            }`}
                                    >
                                        {isRecording ? <><Square size={isEmpty ? 16 : 12} className="fill-current" /> Stop {isEmpty ? "Recording" : ""}</> : <><Mic size={isEmpty ? 16 : 12} /> {isEmpty ? "Start New Encounter" : "Record"}</>}
                                    </motion.button>

                                    {!isEmpty && (
                                        <>
                                            <motion.div layout className={`font-mono text-xs tabular-nums px-2.5 py-1 rounded-md ${isRecording ? "text-red-400 bg-red-500/10" : "text-white/25 bg-white/[0.02]"}`}>
                                                {formatTimer(recordingSeconds)}
                                            </motion.div>
                                            <motion.span layout className={`text-[10px] font-medium flex items-center gap-1.5 ${isProcessing || isRecording ? "text-white/70" : "text-white/30"}`}>
                                                {isProcessing && <span className="w-2.5 h-2.5 rounded-full border-2 border-white/20 border-t-white animate-spin" />}
                                                {status}
                                            </motion.span>
                                            <div className="flex-1" />
                                        </>
                                    )}

                                    {isEmpty && <motion.div layout className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em] my-2 relative before:absolute before:right-full before:mr-4 before:top-1/2 before:-translate-y-1/2 before:w-20 before:h-px before:bg-white/10 after:absolute after:left-full after:ml-4 after:top-1/2 after:-translate-y-1/2 after:w-20 after:h-px after:bg-white/10">Or</motion.div>}

                                    <motion.div layout className={`relative ${isEmpty ? "w-full" : ""}`}>
                                        <select className={`appearance-none bg-white/[0.04] border border-white/10 focus:outline-none cursor-pointer text-white/50 w-full ${isEmpty ? "rounded-xl pl-4 pr-10 py-3 text-sm text-center font-medium" : "rounded-md pl-2.5 pr-6 py-1.5 text-[10px]"}`}>
                                            {micDevices.length > 0 ? micDevices.map((d, i) => (
                                                <option key={d.deviceId || i} value={d.deviceId} className="bg-black text-white">{d.label || `Mic ${i + 1}`}</option>
                                            )) : (
                                                <option>Default Mic</option>
                                            )}
                                        </select>
                                        <ChevronDown size={isEmpty ? 16 : 10} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 pointer-events-none" />
                                    </motion.div>
                                    
                                    <motion.button layout onClick={handleLoadAudio} className={`flex items-center justify-center gap-2 bg-white/[0.04] border border-white/10 hover:border-white/25 text-white/50 hover:text-white transition-all ${isEmpty ? "w-full py-3.5 rounded-xl font-medium text-sm" : "px-3 py-1.5 rounded-md font-medium text-[10px]"}`}>
                                        <Upload size={isEmpty ? 16 : 11} />
                                        {isEmpty ? "Upload Audio File" : "Load Audio"}
                                    </motion.button>
                                </motion.div>
                                
                                {isEmpty && (
                                    <motion.div layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="inline-flex items-center gap-2 px-4 py-2 mt-8 rounded-xl bg-white/[0.02] border border-white/5 text-[10px] text-white/40 font-mono tracking-widest uppercase shadow-lg backdrop-blur-md">
                                        <span className="bg-white/10 px-2 py-1 rounded shadow-[0_1px_0_rgba(255,255,255,0.15)] text-white/80">Ctrl</span> + <span className="bg-white/10 px-2 py-1 rounded shadow-[0_1px_0_rgba(255,255,255,0.15)] text-white/80">R</span> to record
                                    </motion.div>
                                )}
                            </motion.div>

                            {/* Audio player */}
                            {audioUrl && (
                                <motion.div layout initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="px-3 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.06] shrink-0 mt-3">
                                    <audio controls src={audioUrl} className="w-full h-7 opacity-60 hover:opacity-100 transition-opacity" style={{ filter: "invert(1) grayscale(1)" }} />
                                </motion.div>
                            )}

                            {/* Main Grid Area (Only visible when NOT empty) */}
                            {!isEmpty && (
                                <motion.div layout initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex-1 grid grid-cols-2 gap-3 min-h-0 mt-3">
                                    {/* Transcript */}
                                    <section className="glass-panel flex flex-col overflow-hidden">
                            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between shrink-0">
                                <h3 className="text-[10px] font-bold text-white/60 uppercase tracking-wider flex items-center gap-1.5">
                                    <Mic size={12} className={isRecording ? "text-red-400 animate-pulse" : ""} />
                                    Transcript
                                    {isRecording && <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />}
                                </h3>
                                <button onClick={() => handleCopy(transcript)} className="p-1.5 rounded-md hover:bg-white/5 text-white/25 hover:text-white/50 transition-all" title="Copy">
                                    <Copy size={12} />
                                </button>
                            </div>
                            <div className="flex-1 relative min-h-0">
                                <textarea
                                    value={transcript}
                                    onChange={(e) => {
                                        setTranscript(e.target.value);
                                        triggerAutoSave(e.target.value, summary);
                                    }}
                                    placeholder="Transcription will appear here..."
                                    className="absolute inset-0 p-4 text-xs text-white/75 leading-relaxed bg-transparent resize-none focus:outline-none placeholder-white/15 custom-scrollbar"
                                />
                            </div>
                        </section>

                        {/* Clinical Note */}
                        <section className="glass-panel flex flex-col overflow-hidden">
                            <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between shrink-0">
                                <h3 className="text-[10px] font-bold text-white/60 uppercase tracking-wider flex items-center gap-1.5">
                                    <LayoutDashboard size={12} />
                                    Clinical Note
                                </h3>
                                <div className="flex items-center gap-1.5">
                                    <button onClick={handleSummarize} disabled={!activeSessionId || isSummarizing}
                                        className={`p-1.5 rounded-md transition-all ${isSummarizing ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/25 hover:text-white/50"}`} title="Regenerate">
                                        <Sparkles size={12} className={isSummarizing ? "animate-spin" : ""} />
                                    </button>
                                    <button onClick={() => handleCopy(summary)} className="p-1.5 rounded-md hover:bg-white/5 text-white/25 hover:text-white/50 transition-all" title="Copy text">
                                        <Copy size={12} />
                                    </button>
                                    <div className="w-px h-4 bg-white/10 mx-0.5" />
                                    <button disabled
                                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-semibold bg-white/5 text-white/20 cursor-not-allowed border border-transparent"
                                        title="Direct EHR integration is coming soon">
                                        <div className="w-1 h-1 rounded-full bg-indigo-400 animate-pulse" />
                                        EHR Export (Soon)
                                    </button>
                                    <button onClick={handleApproveAndLearn} disabled={!activeSessionId}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[10px] font-semibold transition-all ${activeSessionId
                                            ? "bg-white text-black hover:bg-white/90"
                                            : "bg-white/5 text-white/20 cursor-not-allowed"
                                            }`}>
                                        <ThumbsUp size={10} />
                                        Approve
                                        {feedbackCount > 0 && (
                                            <span className="px-1 py-0.5 rounded-full bg-blue-500/20 text-blue-400 text-[8px] font-bold">
                                                <Brain size={7} className="inline mr-0.5" />{feedbackCount}
                                            </span>
                                        )}
                                    </button>
                                </div>
                            </div>
                            <div className="flex-1 relative min-h-0">
                                {isSummarizing ? (
                                    <div className="absolute inset-0 p-4 flex flex-col gap-3">
                                        <div className="flex items-center gap-2">
                                            <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                                            <p className="text-[10px] text-white/40">Generating clinical note...</p>
                                        </div>
                                        <motion.div animate={{ opacity: [0.05, 0.12, 0.05] }} transition={{ repeat: Infinity, duration: 2 }} className="h-2.5 w-3/4 bg-white/5 rounded" />
                                        <motion.div animate={{ opacity: [0.05, 0.12, 0.05] }} transition={{ repeat: Infinity, duration: 2, delay: 0.3 }} className="h-2.5 w-full bg-white/5 rounded" />
                                    </div>
                                ) : (
                                    <textarea
                                        value={summary}
                                        onChange={(e) => {
                                            setSummary(e.target.value);
                                            triggerAutoSave(transcript, e.target.value);
                                        }}
                                        placeholder="Clinical note will appear here..."
                                        className="absolute inset-0 p-4 text-xs text-white/75 leading-relaxed bg-transparent resize-none focus:outline-none placeholder-white/15 custom-scrollbar"
                                    />
                                )}
                            </div>
                        </section>
                                </motion.div>
                            )}
                        </>
                    );
                })()}
            </div>
        </main>
    );
};
