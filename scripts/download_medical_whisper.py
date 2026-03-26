import os
from pathlib import Path
import ctranslate2.converters.transformers as ct2_tf
import transformers

def patched_load_model(self, model_class, model_name_or_path, **kwargs):
    # Strip the problematic 'dtype' argument if it exists (Transformers 4.47+ compatibility)
    kwargs.pop("dtype", None)
    return model_class.from_pretrained(model_name_or_path, **kwargs)

# Inject the patch
ct2_tf.TransformersConverter.load_model = patched_load_model

def download_and_convert_medical_whisper():
    """
    Downloads Na0s/Medical-Whisper-Large-v3 from HuggingFace
    and converts it to a CTranslate2 optimized model.
    """
    hf_model_id = "Na0s/Medical-Whisper-Large-v3"
    output_dir = "models/medical-whisper-ct2"
    
    if Path(output_dir).exists():
        print(f"[*] Medical Whisper already exists at {output_dir}")
        return

    print(f"[*] Beginning download and conversion of {hf_model_id} via Python API...")
    print("[*] Target format: CTranslate2 (float16) for RTX 3060 optimization")
    
    converter = ct2_tf.TransformersConverter(
        model_name_or_path=hf_model_id
    )
    
    try:
        converter.convert(
            output_dir=output_dir,
            vmap=None,
            quantization="float16",
            force=True
        )
        print(f"\n[+] Successfully converted Medical Whisper!")
        print(f"[+] Model saved to: {output_dir}")
    except Exception as e:
        print(f"[-] An error occurred during conversion: {e}")

if __name__ == "__main__":
    download_and_convert_medical_whisper()
