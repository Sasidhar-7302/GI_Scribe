"use client";

import React, { useState } from "react";
import { User, Shield, Award, Settings, LogOut, Building2, Stethoscope, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const ProfileView = () => {
    const [toast, setToast] = useState<string | null>(null);
    const showToast = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500); };

    return (
        <main className="flex-1 overflow-y-auto bg-black custom-scrollbar">
            <AnimatePresence>
                {toast && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="fixed top-6 right-6 z-50 px-5 py-3 rounded-xl bg-white/10 border border-white/15 text-white text-sm backdrop-blur-xl flex items-center gap-2.5 shadow-lg"
                    >
                        <CheckCircle2 size={14} className="text-blue-400" />
                        {toast}
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="max-w-[1800px] mx-auto px-6 py-6 flex flex-col gap-5">
                <header>
                    <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
                        <User size={22} className="text-white/60" />
                        Physician Profile
                    </h2>
                    <p className="text-xs text-white/40 mt-1">Manage your clinical identity and AI preferences</p>
                </header>

                <div className="grid grid-cols-12 gap-5">
                    {/* Profile card */}
                    <div className="col-span-12 lg:col-span-4">
                        <div className="glass-panel p-6 flex flex-col items-center text-center">
                            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500/80 to-purple-600/80 border border-white/10 mb-4 flex items-center justify-center relative">
                                <User size={32} className="text-white/90" />
                                <div className="absolute bottom-0 right-0 w-4 h-4 bg-emerald-500 border-2 border-black rounded-full" />
                            </div>
                            <h3 className="text-lg font-bold text-white">Dr. Sasidhar</h3>
                            <p className="text-[10px] text-white/40 uppercase tracking-wider mt-1">Chief Gastroenterologist</p>

                            <div className="mt-6 w-full space-y-2.5">
                                <button onClick={() => showToast("System Configuration — coming in v2.0")} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:border-white/20 text-white/60 hover:text-white text-[11px] font-medium transition-all">
                                    <Settings size={13} />
                                    System Configuration
                                </button>
                                <button onClick={() => showToast("Secure Logout — requires auth module (v2.0)")} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:border-white/20 text-white/60 hover:text-white text-[11px] font-medium transition-all">
                                    <LogOut size={13} />
                                    Secure Logout
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Credentials */}
                    <div className="col-span-12 lg:col-span-8">
                        <section className="glass-panel overflow-hidden">
                            <div className="px-5 py-4 border-b border-white/[0.06] flex items-center gap-2">
                                <Shield size={14} className="text-white/50" />
                                <h3 className="text-[11px] font-bold text-white/70 uppercase tracking-wider">Clinical Credentials</h3>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5">
                                {[
                                    { icon: User, label: "Full Name", value: "Sasidhar Y." },
                                    { icon: Award, label: "Medical ID (NPI)", value: "1234567890" },
                                    { icon: Stethoscope, label: "Primary Specialty", value: "Gastroenterology" },
                                    { icon: Building2, label: "Clinical Affiliation", value: "MedRec Health Center" },
                                ].map(({ icon: Icon, label, value }) => (
                                    <div key={label}>
                                        <label className="text-[10px] text-white/30 uppercase tracking-wider block mb-2">{label}</label>
                                        <div className="flex items-center gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/[0.05] text-white/80 text-sm">
                                            <Icon size={14} className="text-white/30" />
                                            {value}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </div>
                </div>
            </div>
        </main>
    );
};
