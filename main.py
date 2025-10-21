#!/usr/bin/env python3
"""
Universal Live Translator Desktop — Professional Edition v4.5
-------------------------------------------------------------
🎙️ Voice Duplication & Advanced Translation Features:
- 🗣️ Voice duplication mode (translate while preserving your voice)
- 🔧 Custom RVC model support (PTH, index, config files)
- 🌍 Multiple translation modes (Standard, Simultaneous, Universal, Voice Duplication)
- 🔗 Platform integrations (Discord, Zoom, Teams, Meet, Slack, Skype)
- 🎮 Gaming features (real-time dubbing, text overlay)
- 📺 Netflix-style resizable overlay (Material Design 3)
- 🚀 GPU acceleration (CUDA/MPS - 10-20x faster)
- ⚡ Advanced async pipeline (parallel processing)
- 💎 Material Design 3 UI (glassmorphic effects)
- 🎬 Smooth animations and micro-interactions
- 📊 Real-time performance monitoring
"""
import sys
import logging
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="ctranslate2")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Setup logging with UTF-8 encoding to handle emojis on Windows
import sys
import io

# Configure handlers with UTF-8 encoding
file_handler = logging.FileHandler('translator.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# For Windows console, wrap stdout to handle UTF-8
if sys.platform == 'win32':
    # Reconfigure stdout to use UTF-8 encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        # Python 3.6 and earlier fallback
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
log = logging.getLogger("Translator")

# Check and install dependencies first
from utils.helpers import ensure_dependencies
ensure_dependencies()

# Now import everything else
from PyQt6.QtWidgets import QApplication
from config.constants import BASE_DIR
from utils import gpu_manager
from ui.main_window_new import LiveTranslatorApp

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Universal Live Translator Pro v4.5")
    app.setStyle("Fusion")
    
    log.info("="*70)
    log.info("🌍 Universal Live Translator — Professional Edition v4.5")
    log.info("="*70)
    log.info(f"📁 Data Directory: {BASE_DIR}")
    log.info(f"🚀 GPU Status: {gpu_manager.device_name}")
    log.info(f"💻 Device: {gpu_manager.device.upper()}")
    log.info(f"⚡ CUDA: {'Available' if gpu_manager.has_cuda else 'Not detected'}")
    log.info(f"🍎 MPS: {'Available' if gpu_manager.has_mps else 'Not detected'}")
    log.info(f"🎨 UI: Material Design 3 (Netflix/Google-level)")
    log.info("="*70)
    
    window = LiveTranslatorApp()
    window.show()
    
    log.info("✅ Application started successfully")
    log.info("💡 Press F1 for help and keyboard shortcuts")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
