Entity-Relationship Diagram (ERD) Entities and Relationships (Strict ERD):

Entities:
- User (user_id, name, email, role)
- Device (device_id, brand, model, user_id)
- DiagnosticSession (session_id, device_id, user_id, start_time, end_time)
- DiagnosticResult (result_id, session_id, fault_code, confidence, timestamp)
- RepairGuide (guide_id, device_id, title, content)
- Technician (technician_id, name, certification, contact)
- Appointment (appointment_id, user_id, technician_id, device_id, datetime, status)

Relationships:
- User owns Device (1-to-many)
- Device has DiagnosticSession (1-to-many)
- DiagnosticSession produces DiagnosticResult (1-to-many)
- Device has RepairGuide (1-to-many)
- User books Appointment (1-to-many)
- Technician handles Appointment (1-to-many)
- Appointment relates to Device (many-to-1)
