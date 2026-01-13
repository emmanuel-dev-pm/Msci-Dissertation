UML Sequence Diagram Entities and Interactions (Strict UML):

Participants:
- User
- Mobile App
- Backend API
- AI/ML Service
- Database
- Technician

Typical Sequence (Device Diagnosis and Repair):
1. User initiates diagnosis in Mobile App
2. Mobile App sends request to Backend API
3. Backend API requests inference from AI/ML Service
4. AI/ML Service returns diagnostic result to Backend API
5. Backend API stores result in Database
6. Backend API returns result to Mobile App
7. Mobile App displays result to User
8. User requests repair guide or technician
9. Mobile App requests guide/technician from Backend API
10. Backend API retrieves guide or notifies Technician
11. Technician responds (if needed)
12. Backend API updates status and notifies Mobile App
13. Mobile App updates User
