# Guided Repair Flow — Wireframe

## Flow Overview
- Entry: Diagnostics result → Start Guided Repair
- Step-by-step video/voice instructions
- Safety checks
- Confirmation and health check

## Wireframe (ASCII)

```
+-----------------------------+
|   Guided Repair Step 1/3    |
+-----------------------------+
| [Video/Voice Clip]          |
|                             |
| Step: Reboot device         |
| Safety: Unplug first!       |
+-----------------------------+
| [ Prev ]   [ Next ]         |
+-----------------------------+
| Progress: ●●○               |
+-----------------------------+
| [ Cancel ]                  |
+-----------------------------+
```

## Click-through Logic
- Next → Next step (update video/text)
- Prev → Previous step
- Cancel → Exit to diagnostics
- Last step Next → Confirmation screen
- Confirmation → Health check → Success/fail
