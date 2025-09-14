  MDSAPP: Technical Overview & System Description

  1. Introduction

  MDSAPP is the core application logic for the Modular Data System 7 (MDS7), an AI-powered platform for advanced data analysis and workflow automation.
  It is built as a monolithic but modular Python application served by a FastAPI web server.

  The system's primary purpose is to provide a secure, multi-user environment where AI agents, powered by Google's Gemini models, can interact with
  data, perform complex tasks, and automate workflows. The architecture is centered around the concept of Casefiles, which act as collaborative,
  data-rich dossiers.

  2. Core Functionalities

   - Casefile Management: Users can create, read, update, and delete Casefiles. These are hierarchical data containers stored in Firestore that aggregate
     various data types. The system enforces a granular, role-based access control (RBAC) model (Admin, Writer, Reader) for each Casefile, ensuring data
     security and integrity.
   - Conversational AI Interaction: The primary user interface is a chat application where users interact with an AI assistant. This interaction is always
     scoped to a specific Casefile, allowing the AI to maintain context. The AI can answer questions, perform actions, and retrieve information relevant to
      the active Casefile.
   - Retrieval-Augmented Generation (RAG): The system can perform semantic searches on documents contained within a Casefile. It uses a
     SentenceTransformer model to generate vector embeddings for document chunks, which are stored and indexed in Firestore. When a user asks a question,
     the RetrievalToolset finds the most relevant document excerpts to provide grounded, accurate answers.
   - Google Workspace Integration: The application is deeply integrated with Google Workspace. AI agents are equipped with tools to:
       - Google Drive: List and search for files within specific date ranges.
       - Gmail: Search for emails, read their content, and process attachments.
       - Google Calendar: List, create, and manage calendar events.
       - Google Docs & Sheets: Create new documents and spreadsheets.
   - Asynchronous Workflow Automation: For long-running tasks, the system uses Prefect to offload work to a separate process. The primary use case is the
     workspace_activity_report_flow, which periodically scans a user's Google Workspace for new activity (files, emails, events) and automatically
     compiles the findings into a new Casefile. This process uses a watermark system to ensure data is not processed redundantly.
   - Real-Time Notifications: The frontend receives real-time status updates for background tasks via a WebSocket connection, which is fed by a Google
     Cloud Pub/Sub topic.
   - System Administration: A separate control panel allows administrators to manage users, change their roles, and view the system's capabilities (i.e.,
     the list of tools available to the AI agents).

  3. Technical Architecture & Frameworks

  MDSAPP is built on a modern Python backend, leveraging several key frameworks and a modular design pattern.

  3.1. Backend Framework: FastAPI

   - The entire backend is built using FastAPI, an asynchronous Python web framework. This provides high performance, automatic OpenAPI/Swagger
     documentation (/docs), and a robust dependency injection system that is used extensively throughout the application.
   - Pydantic is used for all data modeling, validation, and settings management. Every data entity, from API request bodies (CreateCasefileRequest) to
     core database models (Casefile, User), is a strictly-typed Pydantic model, ensuring data consistency.

  3.2. AI & Agent Layer: Google ADK

   - The AI capabilities are built on Google's Agent Development Kit (ADK).
   - `ChatAgent`: This is an LlmAgent that serves as the main conversational assistant. Its key feature is a dynamic instruction provider
     (_provide_instruction), which constructs a new system prompt for every turn. This prompt is rendered from a Jinja2 template stored in Firestore and
     includes up-to-date context about the current user and the active Casefile.
   - `WorkspaceReporterAgent`: This is a BaseAgent with hardcoded, sequential logic. It is not designed for conversation but to execute a specific
     workflow: search Workspace, create a Casefile, and save the results.
   - Toolsets: The connection between agents and the application's business logic is handled by BaseToolset classes (e.g., CasefileToolset,
     GoogleDriveToolset). These toolsets expose methods as FunctionTools that the ChatAgent can call. They act as a crucial abstraction layer,
     translating the agent's intent into calls to the application's core managers and services.

  3.3. Asynchronous Tasks: Prefect

   - Prefect is used to define, orchestrate, and execute long-running, asynchronous workflows. These are defined in the MDSAPP/prefect_flows directory.
   - By offloading tasks like the Google Workspace sync to Prefect, the main FastAPI application remains responsive and is not blocked by I/O-heavy
     operations. Prefect tasks reuse the same core components (managers, services) as the main application, ensuring consistent business logic.

  3.4. Frontend

   - The frontend is a traditional server-side rendered multi-page application built with vanilla HTML, CSS, and JavaScript.
   - It communicates with the FastAPI backend via standard REST API calls for most actions (sending messages, creating casefiles) and uses a WebSocket
     connection to receive real-time push notifications about background tasks.

  4. Cloud Services & Integrations

  MDSAPP is designed to run on Google Cloud Platform (GCP) and leverages several of its services.

   - Vertex AI: Used to run the Gemini 2.5 Flash model, which powers the agents.
   - Firestore: The primary NoSQL database. It stores all application data, including:
       - casefiles: The core data dossiers.
       - users: User accounts and hashed passwords.
       - prompts: Jinja2 templates for the agent's system instructions.
       - adk_sessions: The conversational history and state for each user's chat, managed by the FirestoreSessionService.
       - document_chunks: Text chunks and their vector embeddings for RAG. Firestore's native vector search capability is used here.
   - Google Cloud Pub/Sub: Acts as the messaging backbone. It is used to decouple components and enable real-time features. For example, the
     MdsMonitoringPlugin publishes audit and analytics events to Pub/Sub topics, and the WebSocket notification system uses a dedicated topic per user to
     push updates.
   - Google Cloud Storage: Used by Prefect flows to store large binary artifacts, such as email attachments, before they are linked in a Casefile.
   - Redis: Used as a high-performance, in-memory cache (CacheManager) to store frequently accessed Firestore documents, primarily Casefiles. This reduces
     database load and improves API response times.
   - Google Identity (OAuth 2.0): The application uses OAuth 2.0 to securely access Google Workspace APIs on behalf of the user. The BaseGoogleService
     class manages the token flow, using a downloaded client_secrets.json and a stored token.json to build the API service objects.

  5. Codebase Structure

  The MDSAPP directory is organized by feature and architectural layer, promoting a clean separation of concerns.

   - main.py: The FastAPI application entry point. It initializes the app, sets up middleware, and includes all the API routers.
   - /api/v1/: Contains the FastAPI routers that define the HTTP endpoints. Each file corresponds to a specific resource (e.g., users.py, casefiles.py).
   - /core/: This directory contains the foundational, cross-cutting components of the application.
       - dependencies.py: The heart of the application's service location and dependency injection pattern. It uses @lru_cache to create and provide
         singleton instances of all managers and services, ensuring components are initialized only once and can be easily accessed throughout the app.
       - models/: Defines all Pydantic data models. This provides a single source of truth for the application's data structures.
       - managers/: Contains the core business logic classes (e.g., CasefileManager, CommunicationManager). These classes orchestrate operations but do
         not perform direct external I/O.
       - services/: Contains classes that perform direct I/O with external services (e.g., GoogleDriveService, FirestoreSessionService). They are
         consumed by managers and toolsets.
       - security.py: Handles all authentication and authorization logic, including JWT creation, password hashing, and user validation.
   - /agents/: Defines the ADK agents (ChatAgent, WorkspaceReporterAgent).
   - /toolsets/: Defines the tools available to the agents. These classes bridge the gap between the agent's reasoning loop and the application's core
     logic in the managers.
   - /prefect_flows/: Contains Prefect flow and task definitions for background job processing.
   - /static/: Contains all frontend assets (HTML, CSS, JavaScript).