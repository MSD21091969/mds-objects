# src/core/dependencies.py

import logging
import os
from functools import lru_cache

# --- Core Managers & Utils ---
from src.core.managers.database_manager import DatabaseManager
from src.core.managers.cache_manager import CacheManager
from src.core.managers.prompt_manager import PromptManager
from src.core.managers.pubsub_manager import PubSubManager
from src.core.managers.embeddings_manager import EmbeddingsManager
from src.core.utils.document_parser import DocumentParser
from src.core.services.firestore_session_service import FirestoreSessionService
from src.core.adk_monitoring.service import ADKMonitoringService

# --- Component Services ---
from src.components.casefile.service import CasefileService
from src.components.communication.service import CommunicationService
from src.components.toolsets.retrieval.service import RetrievalService
from src.components.toolsets.web_search.service import WebSearchService
from src.components.toolsets.google_workspace.drive.service import GoogleDriveService
from src.components.toolsets.google_workspace.gmail.service import GoogleGmailService
from src.components.toolsets.google_workspace.docs.service import GoogleDocsService
from src.components.toolsets.google_workspace.sheets.service import GoogleSheetsService
from src.components.toolsets.google_workspace.calendar.service import GoogleCalendarService
from src.components.toolsets.google_workspace.people.service import GooglePeopleService

# --- Component Toolsets ---
from src.components.toolsets.casefile_toolset import CasefileToolset
from src.components.toolsets.retrieval.toolset import RetrievalToolset
from src.components.toolsets.web_search.web_search_toolset import WebSearchToolset
from src.components.toolsets.google_workspace.drive.drive_toolset import DriveToolset
from src.components.toolsets.google_workspace.gmail.gmail_toolset import GmailToolset
from src.components.toolsets.google_workspace.docs.docs_toolset import DocsToolset
from src.components.toolsets.google_workspace.sheets.sheets_toolset import SheetsToolset
from src.components.toolsets.google_workspace.calendar.calendar_toolset import CalendarToolset
from src.components.toolsets.google_workspace.people.people_toolset import PeopleToolset

# --- Agents ---
from src.components.agents.chat_agent import ChatAgent
from src.components.agents.workspace_reporter_agent import WorkspaceReporterAgent

# --- Plugins ---
from src.plugins.logging_plugin import LoggingPlugin
from src.plugins.opentelemetry_plugin import OpenTelemetryMonitoringPlugin
# Import the new plugins from their correct location
from src.plugins.authorization_plugin import AuthorizationPlugin
from src.plugins.cost_tracking_plugin import CostTrackingPlugin
from src.plugins.dynamic_context_plugin import DynamicContextPlugin
from src.plugins.sanitization_plugin import SanitizationPlugin

logger = logging.getLogger(__name__)

# --- Manager Getters ---

@lru_cache(maxsize=None)
def get_database_manager() -> DatabaseManager:
    logger.debug("Creating singleton instance of DatabaseManager")
    return DatabaseManager()

@lru_cache(maxsize=None)
def get_cache_manager() -> CacheManager:
    logger.debug("Creating singleton instance of CacheManager")
    return CacheManager()

@lru_cache(maxsize=None)
def get_prompt_manager() -> PromptManager:
    logger.debug("Creating singleton instance of PromptManager")
    return PromptManager(db_manager=get_database_manager())

@lru_cache(maxsize=None)
def get_casefile_service() -> CasefileService:
    logger.debug("Creating singleton instance of CasefileService")
    return CasefileService(
        db_manager=get_database_manager(),
        cache_manager=get_cache_manager()
    )

@lru_cache(maxsize=None)
def get_pubsub_manager() -> PubSubManager:
    logger.debug("Creating singleton instance of PubSubManager")
    return PubSubManager()

@lru_cache(maxsize=None)
def get_document_parser() -> DocumentParser:
    logger.debug("Creating singleton instance of DocumentParser")
    return DocumentParser()

@lru_cache(maxsize=None)
def get_embeddings_manager() -> EmbeddingsManager:
    logger.debug("Creating singleton instance of EmbeddingsManager")
    return EmbeddingsManager(db_manager=get_database_manager(), parser=get_document_parser())

# --- Monitoring & Plugin Getters ---
@lru_cache(maxsize=None)
def get_adk_monitoring_service() -> ADKMonitoringService:
    logger.debug("Creating singleton instance of ADKMonitoringService")
    return ADKMonitoringService()

@lru_cache(maxsize=None)
def get_logging_plugin() -> LoggingPlugin:
    logger.debug("Creating singleton instance of LoggingPlugin")
    return LoggingPlugin(monitoring_service=get_adk_monitoring_service())

@lru_cache(maxsize=None)
def get_opentelemetry_monitoring_plugin() -> OpenTelemetryMonitoringPlugin:
    logger.debug("Creating singleton instance of OpenTelemetryMonitoringPlugin")
    return OpenTelemetryMonitoringPlugin(
        monitoring_service=get_adk_monitoring_service(),
        app_name="mds7-rebuild" # Ensure this matches the app_name in telemetry_setup
    )

@lru_cache(maxsize=None)
def get_authorization_plugin() -> AuthorizationPlugin:
    logger.debug("Creating singleton instance of AuthorizationPlugin")
    return AuthorizationPlugin()

@lru_cache(maxsize=None)
def get_dynamic_context_plugin() -> DynamicContextPlugin:
    logger.debug("Creating singleton instance of DynamicContextPlugin")
    return DynamicContextPlugin()

@lru_cache(maxsize=None)
def get_cost_tracking_plugin() -> CostTrackingPlugin:
    logger.debug("Creating singleton instance of CostTrackingPlugin")
    return CostTrackingPlugin(monitoring_service=get_adk_monitoring_service())

@lru_cache(maxsize=None)
def get_sanitization_plugin() -> SanitizationPlugin:
    logger.debug("Creating singleton instance of SanitizationPlugin")
    return SanitizationPlugin(monitoring_service=get_adk_monitoring_service())

# --- Service Getters ---

@lru_cache(maxsize=None)
def get_firestore_session_service() -> FirestoreSessionService:
    logger.debug("Creating singleton instance of FirestoreSessionService")
    return FirestoreSessionService(
        db_manager=get_database_manager(),
        monitoring_service=get_adk_monitoring_service()
    )

@lru_cache(maxsize=None)
def get_retrieval_service() -> RetrievalService:
    logger.debug("Creating singleton instance of RetrievalService")
    return RetrievalService()

@lru_cache(maxsize=None)
def get_web_search_service() -> WebSearchService:
    logger.debug("Creating singleton instance of WebSearchService")
    return WebSearchService()

@lru_cache(maxsize=None)
def get_google_drive_service() -> GoogleDriveService:
    logger.debug("Creating singleton instance of GoogleDriveService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GoogleDriveService(client_secrets_path=client_secrets_path)

@lru_cache(maxsize=None)
def get_google_gmail_service() -> GoogleGmailService:
    logger.debug("Creating singleton instance of GoogleGmailService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GoogleGmailService(client_secrets_path=client_secrets_path)

@lru_cache(maxsize=None)
def get_google_docs_service() -> GoogleDocsService:
    logger.debug("Creating singleton instance of GoogleDocsService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GoogleDocsService(client_secrets_path=client_secrets_path)

@lru_cache(maxsize=None)
def get_google_sheets_service() -> GoogleSheetsService:
    logger.debug("Creating singleton instance of GoogleSheetsService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GoogleSheetsService(client_secrets_path=client_secrets_path)

@lru_cache(maxsize=None)
def get_google_calendar_service() -> GoogleCalendarService:
    logger.debug("Creating singleton instance of GoogleCalendarService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GoogleCalendarService(client_secrets_path=client_secrets_path)

@lru_cache(maxsize=None)
def get_google_people_service() -> GooglePeopleService:
    logger.debug("Creating singleton instance of GooglePeopleService")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GooglePeopleService(client_secrets_path=client_secrets_path)

# --- Toolset Getters ---

@lru_cache(maxsize=None)
def get_casefile_toolset() -> CasefileToolset:
    logger.debug("Creating singleton instance of CasefileToolset")
    return CasefileToolset(casefile_service=get_casefile_service())

@lru_cache(maxsize=None)
def get_retrieval_toolset() -> RetrievalToolset:
    logger.debug("Creating singleton instance of RetrievalToolset")
    return RetrievalToolset(retrieval_service=get_retrieval_service())

@lru_cache(maxsize=None)
def get_web_search_toolset() -> WebSearchToolset:
    logger.debug("Creating singleton instance of WebSearchToolset")
    return WebSearchToolset(web_search_service=get_web_search_service())

@lru_cache(maxsize=None)
def get_google_drive_toolset() -> DriveToolset:
    logger.debug("Creating singleton instance of DriveToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return DriveToolset(client_secrets_path=client_secrets_path)


# --- Agent Getters ---

@lru_cache(maxsize=None)
def get_chat_agent() -> ChatAgent:
    logger.debug("Creating singleton instance of ChatAgent")
    return ChatAgent(
        name="ChatAgent",
        model_name="gemini-1.5-flash", # Gebruik een modern, snel model
        prompt_manager=get_prompt_manager(),
        casefile_service=get_casefile_service(),
        # Inject all available toolsets
        tools=[
            get_casefile_toolset(),
            get_retrieval_toolset(),
            get_web_search_toolset(),
            get_google_drive_toolset(),
            get_gmail_toolset(),
            get_google_docs_toolset(),
            get_google_sheets_toolset(),
            get_google_calendar_toolset(),
            get_google_people_toolset(),
        ]
    )

@lru_cache(maxsize=None)
def get_workspace_reporter_agent() -> WorkspaceReporterAgent:
    logger.debug("Creating singleton instance of WorkspaceReporterAgent")
    return WorkspaceReporterAgent(
        name="WorkspaceReporterAgent",
        # This agent performs a specific workflow, so it needs the relevant tools
        tools=[
            get_casefile_toolset(),
            get_google_drive_toolset(),
            get_gmail_toolset(),
            get_google_calendar_toolset(),
        ]
    )

@lru_cache(maxsize=None)
def get_gmail_toolset() -> GmailToolset:
    logger.debug("Creating singleton instance of GmailToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return GmailToolset(client_secrets_path=client_secrets_path)


# --- High-level Manager Getters ---

@lru_cache(maxsize=None)
def get_communication_service() -> CommunicationService:
    logger.debug("Creating singleton instance of CommunicationService")
    # Maak de service aan
    service = CommunicationService(
        session_service=get_firestore_session_service(),
        casefile_service=get_casefile_service(),
        monitoring_service=get_adk_monitoring_service(),
        logging_plugin=get_logging_plugin(),
        opentelemetry_plugin=get_opentelemetry_monitoring_plugin(),
        authorization_plugin=get_authorization_plugin(),
        dynamic_context_plugin=get_dynamic_context_plugin(),
        cost_tracking_plugin=get_cost_tracking_plugin(),
        sanitization_plugin=get_sanitization_plugin(),
    )
    # Injecteer de agent om een circulaire dependency te voorkomen
    service.set_chat_agent(get_chat_agent())
    return service

@lru_cache(maxsize=None)
def get_google_docs_toolset() -> DocsToolset:
    logger.debug("Creating singleton instance of DocsToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return DocsToolset(client_secrets_path=client_secrets_path)


@lru_cache(maxsize=None)
def get_google_sheets_toolset() -> SheetsToolset:
    logger.debug("Creating singleton instance of SheetsToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return SheetsToolset(client_secrets_path=client_secrets_path)


@lru_cache(maxsize=None)
def get_google_calendar_toolset() -> CalendarToolset:
    logger.debug("Creating singleton instance of CalendarToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return CalendarToolset(client_secrets_path=client_secrets_path)


@lru_cache(maxsize=None)
def get_google_people_toolset() -> PeopleToolset:
    logger.debug("Creating singleton instance of PeopleToolset")
    client_secrets_path = os.path.join(os.getcwd(), "client_secrets.json")
    if not os.path.exists(client_secrets_path):
        raise FileNotFoundError(f"client_secrets.json not found at {client_secrets_path}")
    return PeopleToolset(client_secrets_path=client_secrets_path)
