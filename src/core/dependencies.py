# src/core/dependencies.py

import logging
from functools import lru_cache

# Importeer de klassen die we gaan beheren
from src.core.managers.database_manager import DatabaseManager
from src.core.managers.cache_manager import CacheManager
from src.core.managers.prompt_manager import PromptManager
from src.components.casefile_management.manager import CasefileManager
from src.core.services.firestore_session_service import FirestoreSessionService
from src.components.casefile_management.toolset import CasefileToolset
from src.components.agents.chat_agent import ChatAgent
from src.components.communication.manager import CommunicationManager

# NEW Monitoring Imports
from src.core.adk_monitoring.service import ADKMonitoringService
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
def get_casefile_manager() -> CasefileManager:
    logger.debug("Creating singleton instance of CasefileManager")
    return CasefileManager(
        db_manager=get_database_manager(),
        cache_manager=get_cache_manager()
    )

# --- Monitoring Getters (NEW) ---
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

# --- New Plugin Getters ---

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
        monitoring_service=get_adk_monitoring_service() # MODIFIED
    )

# --- Toolset Getters ---

@lru_cache(maxsize=None)
def get_casefile_toolset() -> CasefileToolset:
    logger.debug("Creating singleton instance of CasefileToolset")
    return CasefileToolset(casefile_manager=get_casefile_manager())

# --- Agent Getters ---

@lru_cache(maxsize=None)
def get_chat_agent() -> ChatAgent:
    logger.debug("Creating singleton instance of ChatAgent")
    return ChatAgent(
        name="ChatAgent",
        model_name="gemini-1.5-flash", # Gebruik een modern, snel model
        prompt_manager=get_prompt_manager(),
        casefile_manager=get_casefile_manager(),
        casefile_toolset=get_casefile_toolset()
    )

# --- High-level Manager Getters ---

@lru_cache(maxsize=None)
def get_communication_.manager() -> CommunicationManager:
    logger.debug("Creating singleton instance of CommunicationManager")
    # Maak de manager aan
    manager = CommunicationManager(
        session_service=get_firestore_session_service(),
        casefile_manager=get_casefile_manager(),
        monitoring_service=get_adk_monitoring_service(), # NEW
        logging_plugin=get_logging_plugin(), # NEW
        opentelemetry_plugin=get_opentelemetry_monitoring_plugin(), # NEW
        authorization_plugin=get_authorization_plugin(),
        dynamic_context_plugin=get_dynamic_context_plugin(),
        cost_tracking_plugin=get_cost_tracking_plugin(),
        sanitization_plugin=get_sanitization_plugin(),
    )
    # Injecteer de agent om een circulaire dependency te voorkomen
    manager.set_chat_agent(get_chat_agent())
    return manager