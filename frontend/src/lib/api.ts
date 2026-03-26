const API_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws";

async function safeFetch(url: string, options?: RequestInit) {
    try {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch {
        // Backend is offline or unreachable — return graceful defaults
        return null;
    }
}

export const api = {
    async getStatus() {
        return await safeFetch(`${API_URL}/status`) ?? { is_recording: false, gpu_label: "Offline", summarizer_ready: false };
    },

    async startRecording() {
        const data = await safeFetch(`${API_URL}/record/start`, { method: "POST" });
        if (!data) throw new Error("Backend unreachable. Start the API server first.");
        return data;
    },

    async stopRecording(id: string) {
        const data = await safeFetch(`${API_URL}/record/stop/${id}`, { method: "POST" });
        if (!data) throw new Error("Backend unreachable.");
        return data;
    },

    async listSessions() {
        return await safeFetch(`${API_URL}/sessions`) ?? [];
    },

    async getSession(id: string) {
        const data = await safeFetch(`${API_URL}/sessions/${id}`);
        if (!data) throw new Error("Session not found or backend offline.");
        return data;
    },

    async updateSession(id: string, data: { transcript?: string; summary?: string; label?: string }) {
        const result = await safeFetch(`${API_URL}/sessions/${id}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!result) throw new Error("Failed to save — backend offline.");
        return result;
    },

    async updateSessionLabel(id: string, label: string) {
        const result = await safeFetch(`${API_URL}/sessions/${id}/label`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ label }),
        });
        if (!result) throw new Error("Failed to save label");
        return result;
    },

    getAudioUrl(id: string) {
        return `${API_URL}/sessions/${id}/audio`;
    },

    async summarizeSession(id: string) {
        const data = await safeFetch(`${API_URL}/sessions/${id}/summarize`, { method: "POST" });
        if (!data) throw new Error("Summarization failed — backend offline.");
        return data;
    },



    connectWS(onMessage: (data: unknown) => void) {
        const ws = new WebSocket(WS_URL);
        ws.onmessage = (event) => {
            onMessage(JSON.parse(event.data));
        };
        ws.onerror = () => {
            console.warn("WebSocket connection failed — backend may be offline.");
        };
        return ws;
    },

    // ── Audio Upload ────────────────────────────────────────────────

    async uploadAudio(file: File) {
        const formData = new FormData();
        formData.append("file", file);
        try {
            const res = await fetch(`${API_URL}/upload`, { method: "POST", body: formData });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        } catch {
            throw new Error("Upload failed — is the backend running?");
        }
    },

    // ── Adaptive Learning ──────────────────────────────────────────

    async approveSession(id: string) {
        const data = await safeFetch(`${API_URL}/sessions/${id}/approve`, { method: "POST" });
        return data ?? { status: "offline" };
    },

    async getPreferences() {
        return await safeFetch(`${API_URL}/preferences`) ?? { preferences: [], feedback_count: 0, preference_count: 0 };
    },

    async resetPreferences() {
        const data = await safeFetch(`${API_URL}/preferences/reset`, { method: "POST" });
        return data ?? { status: "offline" };
    }
};
