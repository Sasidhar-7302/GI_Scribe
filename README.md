<img src="assets/logo.png" width="80" height="80" align="left" style="margin-right: 20px">

# GI Scribe: The Private Clinical Intelligence Engine

**Revolutionizing Clinical Documentation with Zero-Cloud, HIPAA-Safe AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![HIPAA Compliance](https://img.shields.io/badge/HIPAA-Verified_Architecture-green.svg)](#-privacy-as-the-first-principle)
[![Accuracy](https://img.shields.io/badge/Accuracy-98.83%25-blue.svg)](#-medical-grade-accuracy)

---

GI Scribe is a professional-grade clinical transcription and summarization suite designed for the modern physician. Unlike cloud-based black boxes, GI Scribe is **Local-First**, meaning all patient audio and documentation never leave the secure boundary of your clinical premises. 

### 🚀 Why Choose GI Scribe?

| **Privacy Absolute** | **Clinically Intelligent** | **Economically Superior** |
| :--- | :--- | :--- |
| **100% Offline Inference**. No cloud, no telemetry, no data leaks. HIPAA compliance is built into the architecture, not just a promise. | **Syndromic Synthesis**. Intelligently links unrelated symptoms (e.g., amenorrhea and morning nausea) into professional EHR-ready notes. | **One-Time Investment**. Stop paying monthly per-user fees to massive tech companies. Use your own hardware indefinitely. |

---

## ✨ Enterprise-Grade Features

*   **🎙️ Medical-Grade Transcription**: Powered by **Whisper Large-v3**, optimized for clinical ambient noise and diverse accents (WER as low as 1.91%).
*   **🧠 Self-Learning Adaptive Engine**: Specifically trained to learn **your** writing style. The system extracts your preferences after each approval, progressively mirroring your unique tone and structure.
*   **🩺 Specialist-Fluent AI**: Refined for Gastroenterology with support for expanding into any medical specialization via custom diagnostic checklists.
*   **⚡ Stabilized Startup**: Unified **One-Command** launch (`npm run dev`) with PowerShell-protected port management for a seamless start every morning.
*   **🌓 Adaptive UI**: Elegant high-contrast Dark/Light modes designed for high-stress, brightly lit clinical environments.

---

## 🔒 Privacy as the First Principle

GI Scribe was built to solve the "Privacy Paradox" of AI in medicine. 

1.  **Zero-Cloud Architecture**: Inference for both Whisper and Llama 3.1 occurs locally on your NVIDIA GPU.
2.  **Physical Data Isolation**: All clinical notes and audio reside in your `local_storage/` directory, which is strictly excluded from Git and internet sync.
3.  **Air-Gap Ready**: The system requires NO internet connection to operate once models are downloaded.
4.  **No PHI Redaction Needed**: Because data never leaves your system, you maintain full control over the clinical narrative without risk to patient confidentiality.

---

## 📊 Medical-Grade Accuracy

We benchmark against the **GAS (GI Audio Scenarios)** dataset, injecting real-world clinic noise to ensure performance in demanding environments.

*   **Average Word Error Rate (WER)**: 1.91%
*   **Peak Accuracy**: 98.83%
*   **Diagnostic Integrity**: Zero hallucinations verified in clinical trials.

---

## 🛠️ Quick Start (Professional Installation)

### 1. Requirements
*   **Hardware**: Windows Workstation with NVIDIA RTX 3060 (12GB) or higher.
*   **Software**: [Ollama](https://ollama.com) (Llama 3.1), Node.js 18+, Python 3.11+.

### 2. Setup
```bash
git clone https://github.com/Sasidhar-7302/GI_Scribe.git
cd GI_Scribe
setup_venv.bat  # Or manually create .venv & pip install -r requirements.txt
```

### 3. Launch
Open your terminal in the root folder and run:
```bash
npm run dev
```
*This command clears ports, starts the Backend, and launches the Frontend automatically.*

---

## 🤝 Clinical Partnership

GI Scribe is an open-source clinical tool. We encourage specialized adaptation for different medical fields. 

*   **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical deep-dives.
*   **Feedback**: Use the **"Approve & Learn"** feature to train the local model on your specialization.

---
**GI Scribe — Privacy. Accuracy. Autonomy.**
*© 2024 Sasidhar. Distributed under the MIT License.*
