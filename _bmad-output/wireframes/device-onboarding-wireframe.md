# Device Onboarding — Wireframe

## Flow Overview
- Entry: Home screen → Add Device
- Options: Scan QR / Manual Entry
- Device pairing (Wi-Fi/BLE)
- Telemetry opt-in
- Success confirmation

## Wireframe (ASCII)

```
+-----------------------------+
|        Add Device           |
+-----------------------------+
| [ Scan QR ]   [ Manual ]    |
+-----------------------------+
| Device List                 |
|  - Camera 1 (online)        |
|  - Speaker (offline)        |
+-----------------------------+
| [ Pair Device ]             |
+-----------------------------+
| Telemetry: [x] Opt-in       |
+-----------------------------+
|   [ Confirm ]               |
+-----------------------------+
```

## Click-through Logic
- Scan QR → Camera permission → Device found → Pair Device
- Manual → Enter code → Pair Device
- Pair Device → Telemetry opt-in → Confirm → Success
