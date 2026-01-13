Data Flow Diagram Entities and Data Exchanges (for Excalidraw):

Entities:
- User
- Mobile App
- Backend API
- AI/ML Service
- Database (Firebase)
- Technician
- Device

Data Flows:
- User inputs data into Mobile App
- Mobile App sends user/device data to Backend API
- Backend API forwards relevant data to AI/ML Service for diagnostics
- AI/ML Service returns diagnostic results to Backend API
- Backend API stores/retrieves data from Database
- Backend API sends results and repair guides to Mobile App
- Mobile App displays results to User
- Device sends telemetry data to Backend API
- Technician receives requests and sends responses via Backend API
