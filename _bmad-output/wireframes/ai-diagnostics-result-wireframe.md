# AI Diagnostics Result — Wireframe

## Flow Overview
- Entry: Device detail → Run Diagnostics
- AI runs checks
- Result: Plain-language summary, confidence score, next action

## Wireframe (ASCII)

```
+-----------------------------+
|   Diagnostics Result        |
+-----------------------------+
| Device: Camera 1            |
| Status: Offline             |
|-----------------------------|
| Issue: Firmware mismatch    |
| Confidence: 92%             |
|-----------------------------|
| [ Start Guided Repair ]     |
| [ Escalate to Technician ]  |
+-----------------------------+
| Details ▼                   |
+-----------------------------+
```

## Click-through Logic
- Run Diagnostics → Show result
- Start Guided Repair → Guided repair flow
- Escalate → Technician booking
- Details ▼ → Expand for logs/telemetry
