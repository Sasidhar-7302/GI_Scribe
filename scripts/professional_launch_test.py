import os
import sys
import platform
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("PreLaunchTest")

def _print_header(title: str):
    logger.info("=" * 60)
    logger.info(f"[{title}]")
    logger.info("=" * 60)

def test_environment_and_dependencies():
    _print_header("TEST 1: OS Environment & Python Dependencies")
    logger.info(f"OS Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    logger.info(f"Python Version: {sys.version.split(' ')[0]}")
    
    try:
        import PySide6
        logger.info(f"PySide6 (GUI): PASS (v{PySide6.__version__})")
    except ImportError as e:
        logger.error(f"PySide6 Failed: {e}")
        return False
        
    try:
        import faster_whisper
        import ctranslate2
        logger.info(f"faster-whisper (Audio AI): PASS")
        logger.info(f"ctranslate2 (AI Driver): PASS (v{ctranslate2.__version__})")
    except ImportError as e:
        logger.error(f"Whisper/CT2 Failed: {e}")
        return False
        
    try:
        import ollama
        logger.info(f"Ollama (LLM Bindings): PASS")
    except ImportError as e:
        logger.error(f"Ollama Client Failed: {e}")
        return False
        
    return True

def test_hardware_resolver():
    _print_header("TEST 2: Dynamic Hardware Auto-Detection")
    try:
        from app.hardware import detect_and_configure_gpu
        index = detect_and_configure_gpu()
        if index is not None:
            logger.info(f"Hardware Resolver correctly initialized and targeted GPU {index}.")
            logger.info(f"Validated ENV INJECTIONS: CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES')} / OLLAMA_VISIBLE_DEVICES={os.environ.get('OLLAMA_VISIBLE_DEVICES')}")
        else:
            logger.info("Hardware Resolver detected CPU-only mode.")
        return True
    except Exception as e:
        logger.error(f"Hardware Resolver Crashed: {e}")
        return False

def test_configuration_integrity():
    _print_header("TEST 3: Configuration & Model Availability")
    from app.config import AppConfig
    try:
        config = AppConfig.load()
        logger.info(f"Config Load: PASS")
        logger.info(f"Target Whisper Model: {config.whisper.faster_model}")
        logger.info(f"Target LLM Summarizer: {config.summarizer.model}")
        
        # Verify the offline model exists in the huggingface cache
        models_dir = Path("models/faster-whisper")
        target_model = f"models--Systran--faster-whisper-{config.whisper.faster_model}"
        if not (models_dir / target_model).exists():
            logger.warning(f"Target fallback model directory ({target_model}) not strictly found in {models_dir}. Ensure network is allowed for first run or download manually.")
        else:
            logger.info("Local Whisper Model Checkpoint: PASS")
            
        return True
    except Exception as e:
        logger.error(f"Config Integrity Failed: {e}")
        return False

def run_all_tests():
    logger.info("Starting Professional Pre-Launch Diagnostic Suite...")
    
    tests = [
        test_environment_and_dependencies,
        test_hardware_resolver,
        test_configuration_integrity
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            logger.error(f"--- FAILURE IN: {test.__name__} ---")
            break
            
    _print_header("DIAGNOSTIC SUMMARY")
    if passed == len(tests):
        logger.info("ALL SYSTEMS GO. The application is ready for PyInstaller compiling.")
        sys.exit(0)
    else:
        logger.error(f"FAILED {len(tests) - passed} checks. Resolve issues before building the .exe.")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
