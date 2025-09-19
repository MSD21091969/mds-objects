 # MDSAPP - Tiny Data Collider

## 1. Introduction

MDSAPP is an advanced, modular Python platform designed to analyze large volumes of heterogeneous data using AI agents. [cite_start]Built as a **monolithic but modular** application served by a FastAPI web server [cite: 12][cite_start], its primary purpose is to provide a secure, multi-user environment where **AI agents, powered by Google's Gemini models**, can interact with data and automate complex tasks[cite: 13]. [cite_start]The core of the architecture is the **Casefile** concept, which acts as a collaborative, data-rich dossier[cite: 14].

## 2. Core Functionalities

* [cite_start]**Casefile Management**: Users can create, read, update, and delete Casefiles[cite: 15]. [cite_start]These are hierarchical data containers stored in Firestore that aggregate various data types[cite: 16]. [cite_start]The system enforces a granular, role-based access control (RBAC) model (Admin, Writer, Reader) for each Casefile, ensuring data security and and integrity[cite: 17].
* [cite_start]**Conversational AI Interaction**: The primary user interface is a chat application where users interact with an AI assistant[cite: 18]. [cite_start]This interaction is always scoped to a specific Casefile, allowing the AI to maintain context[cite: 19]. [cite_start]The AI can answer questions, perform actions, and retrieve information relevant to the active Casefile[cite: 20].
* [cite_start]**Retrieval-Augmented Generation (RAG)**: The system can perform semantic searches on documents contained within a Casefile[cite: 21]. [cite_start]It uses a SentenceTransformer model to generate vector embeddings for document chunks, which are stored and indexed in Firestore[cite: 22, 54]. [cite_start]When a user asks a question, the RetrievalToolset finds the most relevant document excerpts to provide grounded, accurate answers[cite: 23].
* [cite_start]**Google Workspace Integration**: The application is deeply integrated with Google Workspace[cite: 24]. [cite_start]AI agents are equipped with tools to list and search for files, search and read emails, and manage calendar events[cite: 25, 26, 27].
* [cite_start]**Asynchronous Workflow Automation**: For long-running tasks, the system uses **Prefect** to offload work to a separate process[cite: 28]. [cite_start]The primary use case is the `workspace_activity_report_flow`, which periodically scans a user's Google Workspace for new activity and automatically compiles the findings into a new Casefile[cite: 28].
* [cite_start]**Real-Time Notifications**: The frontend receives real-time status updates for background tasks via a **WebSocket connection**, which is fed by a Google Cloud Pub/Sub topic[cite: 30].

## 3. Technical Architecture & Frameworks

The architecture of MDSAPP is modern, modular, and based on a clear separation of concerns.

### 3.1. Backend Framework: FastAPI & SAMT

* [cite_start]**FastAPI**: The entire backend is built using FastAPI, which provides high performance, automatic OpenAPI/Swagger documentation, and a robust dependency injection system used extensively throughout the application[cite: 33, 34].
* [cite_start]**Pydantic**: Pydantic is used for all data modeling, validation, and settings management[cite: 35]. [cite_start]Every data entity, from API request bodies to core database models, is a strictly-typed Pydantic model, ensuring data consistency[cite: 36].
* **SAMT Architecture**: The application follows a layered `Service` (Managers), `API`, `Model`, and `Toolset` pattern, which is the key to its reusability and maintainability.

### 3.2. AI and Agent Layer: Google ADK

* [cite_start]**Google ADK**: The AI capabilities are built on Google's Agent Development Kit[cite: 37].
* [cite_start]**Agents**: The `ChatAgent` serves as the main conversational assistant[cite: 38]. [cite_start]Its key feature is a dynamic instruction provider, which constructs a new system prompt for every turn from a Jinja2 template stored in Firestore[cite: 39, 40]. [cite_start]The `WorkspaceReporterAgent` is designed to execute specific, hardcoded workflows[cite: 41].
* [cite_start]**Toolsets**: The connection between agents and the application's business logic is handled by `BaseToolset` classes, which expose methods as `FunctionTools` that the `ChatAgent` can call[cite: 42, 43]. [cite_start]These toolsets act as a crucial abstraction layer, translating the agent's intent into calls to the application's core managers and services[cite: 44].

### 3.3. Cloud Services & Integrations

[cite_start]The application is designed to run on Google Cloud Platform (GCP) and leverages several of its services[cite: 50]:

* [cite_start]**Firestore**: The primary NoSQL database[cite: 51]. [cite_start]It stores all application data, including Casefiles [cite: 52][cite_start], users, and conversational history[cite: 53]. [cite_start]Its native vector search capability is used to store and index document chunks and their embeddings for RAG[cite: 54].
* [cite_start]**Google Cloud Pub/Sub**: Acts as the messaging backbone[cite: 55]. [cite_start]It is used to decouple components and enable real-time features, such as pushing updates to the frontend[cite: 56].
* [cite_start]**Google Cloud Storage**: Used by Prefect flows to store large binary artifacts, such as email attachments[cite: 57].
* [cite_start]**Redis**: Used as a high-performance, in-memory cache to store frequently accessed Firestore documents[cite: 58, 59].

## 4. Future Plans

The architecture is designed to expand with new functionalities. The focus is on extending diagnostics and refining ADK integration with:

* **Advanced ADK Plugins**: Development of custom plugins, including `AuthorizationPlugin`, `CostTrackingPlugin`, and `SanitizationPlugin`, alongside the existing `LoggingPlugin` and `OpenTelemetryMonitoringPlugin`.
* **Callback Patterns**: Further implementation of callback patterns for real-time monitoring and interaction.
* **`ToolContext` Enhancements**: Deeper use of the `ToolContext` state to influence workflow execution and enable more complex interactions between tools.

This is the next step in the application's transformation into a "Tiny Data Collider".
