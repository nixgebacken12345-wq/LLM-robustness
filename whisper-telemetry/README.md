# Whisper Telemetry Collector

**Version:** 2.0.0  
**Platform:** Windows 10/11 (x64)  
**Purpose:** Enterprise endpoint diagnostic and keyboard input telemetry

## Overview

Whisper Telemetry Collector is an authorized IT diagnostic tool for:
- Keyboard input latency analysis
- User workflow optimization
- Application usability testing
- Security incident investigation (authorized only)

## Installation

```bash
pip install -r requirements.txt
python setup.py install
```

Configuration

Copy .env.example to .env and configure:

  WHISPER_TELEMETRY_ENDPOINT (internal IT endpoint)
  WHISPER_TELEMETRY_KEY (API authentication)

  Usage

 python src/main.py --service install
 net start WhisperTelemetry

 Legal

Authorized use only. Unauthorized access violates company policy.


---

