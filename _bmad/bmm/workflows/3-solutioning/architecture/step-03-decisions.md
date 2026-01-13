---
step: 3
name: Architectural Decisions
status: pending
---

# Step 3: Architectural Decisions

In this step, we will identify and make key architectural decisions for the Techare Ai Research Project. These decisions will guide the technical direction and ensure alignment with project goals and constraints.

## Instructions
Please address the following:
1. What are the most critical architectural decisions for this project? (e.g., technology stack, integration approach, data flow, security, scalability)
2. For each decision, provide:
   - The options considered
   - The rationale for the chosen option
   - Any trade-offs or risks


## Architectural Decisions

**Mobile App Stack:**
Option: React Native vs. Native Android vs. Flutter
Chosen: React Native
Rationale: Supports rapid cross-platform prototyping and consistent UX during user evaluation.
Trade-offs: Hardware-level features may require native extensions in later iterations.

**AI/ML Approach:**
Option: Server-side Python-based inference (scikit-learn) vs. on-device models
Chosen: Server-side Python-based inference
Rationale: Enables rapid experimentation, retraining, and controlled evaluation.
Trade-offs: Increased dependency on network connectivity and potential inference latency.

**Integration Method:**
Option: RESTful API vs. embedded integration vs. gRPC
Chosen: RESTful API
Rationale: Simplicity, transparency, and ease of debugging in academic research context.
Trade-offs: Latency risks mitigated through response caching and batched requests.

**Data Flow:**
Option: Request–response vs. asynchronous/message queue
Chosen: Request–response with optional async processing
Rationale: Reduces system complexity at MVP stage.
Trade-offs: Message queues may be required in future to prevent bottlenecks under increased load.

**Backend & Storage:**
Option: Firebase (Firestore/Realtime Database) vs. Node.js (Express.js) with PostgreSQL vs. Python (Django/Flask) vs. NoSQL (MongoDB)
Chosen: Firebase (Firestore/Realtime Database)
Rationale: Firebase provides a fully managed backend with real-time data sync, built-in authentication, and offline support, enabling rapid development and seamless integration with React Native. It reduces operational overhead and is ideal for mobile-first applications.
Trade-offs: Less flexibility for complex relational queries, potential vendor lock-in, and limited control over backend infrastructure compared to self-hosted solutions.

**Security & Privacy:**
Option: Privacy-by-design vs. data-rich approach
Chosen: Privacy-by-design
Rationale: Minimal data collection, encryption, anonymisation.
Trade-offs: Reduced data availability may constrain early-stage model performance.

**Offline Support:**
Option: Offline-first vs. online-only
Chosen: Hybrid offline-first
Rationale: Repair guides and basic triage work offline; AI diagnosis requires connectivity.
Trade-offs: Balances resilience/usability against app size/complexity.

**Scalability:**
Option: Containerised horizontal scaling vs. monolithic scaling
Chosen: Containerised services with horizontal scaling
Rationale: Supports future growth and independent scaling of components.
Trade-offs: Cold-start latency risk during early deployment.

**Observability:**
Option: Basic logging/monitoring vs. none
Chosen: Basic logging and error monitoring
Rationale: Supports evaluation, debugging, and performance analysis.
Trade-offs: Modest upfront development overhead for improved reliability.