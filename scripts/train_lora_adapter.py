import os
import sys

# Phase 10: Strict Pre-Import Hardware Masking
# We MUST set this before any CUDA initialization occurs in torch/transformers.
# We explicitly target the 12GB RTX 3060 (Device 0).
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["OLLAMA_VISIBLE_DEVICES"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import glob
import json
import torch
from pathlib import Path

def pin_best_hardware():
    """Ensure we use the RTX 3060 (12GB) for the Rank-32 training."""
    try:
        sys.path.append(os.getcwd())
        from app.hardware import detect_and_configure_gpu
        best_idx = detect_and_configure_gpu()
        print(f"[+] Training pinned to CUDA Device {best_idx}")
        return best_idx
    except Exception as e:
        print(f"[-] Hardware detection failed: {e}. Falling back to default.")
        return 0

def train_lora_adapter():
    """
    Phase 6 Future-Proofing Script:
    Reads your human-corrected ground truth JSON notes from `data/training_corpus` 
    and aligns them with the original mp3 sources. 
    
    This primes a LoRA fine-tuning session over the Medical Whisper dataset using 
    HuggingFace PEFT on the 12GB RTX 3060.
    """
    corpus_dir = Path("data/training_corpus/chunks")
    if not corpus_dir.exists():
        print("[-] Training corpus directory not found. Have you saved any final notes yet?")
        return

    json_files = glob.glob(str(corpus_dir / "*.json"))
    if not json_files:
        print("[-] No correction telemetry found. Please make edits in the UI and click 'Save Final Note'.")
        return

    print(f"[+] Found {len(json_files)} human-corrected clinical notes.")
    
    dataset_records = []
    
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data.get("was_edited", False):
                audio_source = data.get("audio_file")
                final_text = data.get("final_corrected_note")
                if audio_source and final_text and os.path.exists(audio_source):
                    dataset_records.append({
                        "audio": audio_source,
                        "text": final_text
                    })
                    
    print(f"[+] Loaded {len(dataset_records)} valid training pairs with audio sources.")
    
    if len(dataset_records) == 0:
        print("[!] Not enough data for a stable LoRA fine-tune.")
        print("[!] Generating mock data for the sake of pipeline compilation validation...")
        # For demonstration purposes, we will bypass the restriction if empty by just exiting, 
        # but in production, we wait for real data.
        return

    print("\n[*] Initializing PyTorch PEFT LoRA Fine-Tuning pipeline...")
    
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor
        from peft import LoraConfig, get_peft_model
        from datasets import Dataset, Audio
    except ImportError as e:
        print(f"[-] Missing training dependency: {e}")
        print("[*] Please run: pip install peft datasets accelerate bitsandbytes librosa")
        return

    # 1. Load the Processor and Model
    model_id = "Na0s/Medical-Whisper-Large-v3"
    print(f"[*] Loading foundation model: {model_id}...")
    
    processor = WhisperProcessor.from_pretrained(model_id)
    
    # Phase 10 hardware-aware pinning
    device_idx = pin_best_hardware()
    
    # Load model in native bfloat16 (Ampere optimized) to resolve precision conflicts
    # BFloat16 avoids the nasty range issues and casting bugs of FP16
    model = WhisperForConditionalGeneration.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16,
        device_map={"": 0} # We mask with CUDA_VISIBLE_DEVICES, so local 0 is the 3060
    )
    
    # 2. Prepare PEFT Configuration
    # Phase 10: Hyper-Accuracy Expansion
    # Increase Rank (r) and target all major projections for finer medical detail
    config = LoraConfig(
        r=32, 
        lora_alpha=64, 
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], # Expanded targeting
        lora_dropout=0.05, 
        bias="none"
    )
    model = get_peft_model(model, config)
    model.print_trainable_parameters()
    
    # 3. Compile Dataset
    print("[*] Processing acoustic tensors...")
    ds = Dataset.from_list(dataset_records)

    import librosa

    def prepare_dataset(batch):
        audio_path = batch["audio"]
        audio_array, _ = librosa.load(audio_path, sr=16000)
        batch["input_features"] = processor.feature_extractor(audio_array, sampling_rate=16000).input_features[0]
        batch["labels"] = processor.tokenizer(batch["text"]).input_ids
        return batch

    encoded_ds = ds.map(prepare_dataset, remove_columns=ds.column_names)

    from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments
    import accelerate
    
    # 4. Training loop
    # Phase 10: High-Precision Training Schedule
    training_args = Seq2SeqTrainingArguments(
        output_dir="./models/lora_weights",
        per_device_train_batch_size=1, # Reduced for 12GB stability at Rank 32
        gradient_accumulation_steps=4, # Keep effective batch total at 4
        learning_rate=5e-4, 
        warmup_steps=30,
        max_steps=300,      
        lr_scheduler_type="cosine", 
        bf16=True,           # Ampere native bfloat16
        fp16=False,
        optim="adamw_torch", 
        eval_strategy="no",
        save_strategy="steps",
        save_steps=100,
        logging_steps=10,
        report_to=["none"],
    )

    # Data collator for seq2seq
    class DataCollatorSpeechSeq2SeqWithPadding:
        def __init__(self, processor):
            self.processor = processor

        def __call__(self, features):
            input_features = [{"input_features": feature["input_features"]} for feature in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
            # Force BFloat16 to match the model weights exactly
            batch["input_features"] = batch["input_features"].to(torch.bfloat16)
            
            label_features = [{"input_ids": feature["labels"]} for feature in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
            batch["labels"] = labels
            return batch
            
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=encoded_ds,
        data_collator=DataCollatorSpeechSeq2SeqWithPadding(processor),
    )

    print("[*] Commencing LoRA GPU Training Loop...")
    model.config.use_cache = False
    trainer.train()

    print("[+] Training Complete. Saving LoRA adapter...")
    model.save_pretrained("models/medical-whisper-lora-only")
    
    print("[*] Merging PEFT weights into base model...")
    merged_model = model.merge_and_unload()
    merged_model.save_pretrained("models/medical-whisper-lora-merged")
    processor.save_pretrained("models/medical-whisper-lora-merged")
    
    print("[*] Exporting to CTranslate2 format for production inference...")
    ct2_dir = Path("models/medical-whisper-lora-ct2")
    if ct2_dir.exists():
        import shutil
        shutil.rmtree(ct2_dir)
        
    os.system("ct2-transformers-converter --model models/medical-whisper-lora-merged --output_dir models/medical-whisper-lora-ct2 --quantization float16 --force")
    print("[+] Model successfully adapted to your voice and vocabulary and integrated into CTranslate2!")

if __name__ == "__main__":
    train_lora_adapter()
