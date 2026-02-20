# GI Scribe

**A Professional, Local-First AI Medical Scribe for Gastroenterology.**

GI Scribe listens to patient encounters, transcribes audio with high fidelity, polishes the transcript for medical accuracy, and generates structured clinical notes (HPI, Assessment, Plan). Designed specifically for Gastroenterology, it prioritizes patient privacy by running **100% offline**.

## ✨ Key Features

*   **Three-Stage Intelligence Pipeline:**
    1.  **Transcribe:** Utilizes OpenAI Whisper (`large-v3`, C++ optimized) for high-accuracy speech-to-text.
    2.  **Polish:** Refines transcripts using MedLlama3 to ensure verbatim correction while preserving crucial conversational context.
    3.  **Summarize:** Generates clinical notes directly from polished text, strictly adhering to medical structures.
*   **Zero-Hallucination Framework:** Strict safeguards ensure the AI explicitly denotes "Not Documented" for missing information, preventing dangerous fabricated clinical data.
*   **Complete Privacy:** No cloud APIs. No data leaves your machine. HIPAA-compliant by design.
*   **Modern UI:** A beautiful, responsive PySide6 interface optimized for high-speed clinical workflows.

## 📂 Project Structure

*   `app/`: Core application logic.
    *   `ui/`: Modular UI framework (`main_window.py`, `components.py`, `styles.py`).
    *   *Backend engines* (`transcriber.py`, `summarizer.py`, `storage.py`).
*   `data/`: Validation and testing datasets.
*   `models/`: Binary model files (GGML/GGUF).
*   `scripts/`: Utility scripts for benchmarking, data generation, and maintenance.

## 🛠️ Installation & Setup

### 1. Python Environment
Requires Python 3.11+.
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Whisper Backend (C++)
The engine uses heavily optimized C++ bindings for inference speed.
```powershell
git clone https://github.com/ggerganov/whisper.cpp external\whisper.cpp
cd external\whisper.cpp
cmake -B build -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release
```
Place `ggml-large-v3.bin` into `models\whisper`.

### 3. Ollama Integration
Install [Ollama](https://ollama.com/) and fetch the Llama3 backbone:
```powershell
ollama pull llama3
```
Ensure the background service `ollama serve` is running.

### 4. Configuration
Duplicate `config.example.json` and rename it to `config.json`. Update paths as necessary to match your environment.

## ▶️ Usage

To launch the GI Scribe interface:
```powershell
python main.py
```

## 🧪 Verification & Benchmarking
Run the full end-to-end pipeline test to validate accuracy on your hardware:
```powershell
python scripts/validate_full_pipeline.py
```

## 📄 Documentation
For detailed system design and flow state, review [ARCHITECTURE.md](ARCHITECTURE.md).
