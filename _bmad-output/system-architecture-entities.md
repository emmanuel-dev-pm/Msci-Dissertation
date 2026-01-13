System Architecture Diagram Entities and Relationships (Strict UML):

Entities:
- Mobile App (React Native)
- Backend API (RESTful)
- AI/ML Service (Python Inference)
- Database (Firebase)
- User
- Technician
- Device

Relationships:
- User interacts with Mobile App
- Mobile App communicates with Backend API
- Backend API queries AI/ML Service for diagnostics
- Backend API reads/writes to Database
- Mobile App displays Device data and repair guides
- Technician receives requests from Mobile App via Backend API
- Device sends telemetry to Backend API
