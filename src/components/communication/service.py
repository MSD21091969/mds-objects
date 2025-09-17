# src/components/communication/service.py

import logging
from typing import Any, Dict
from fastapi import HTTPException

from google.adk.runners import Runner
from google.genai import types as genai_types

from src.core.models.user import User
from src.core.services.firestore_session_service import FirestoreSessionService
from src.components.casefile.service import CasefileService
from src.core.adk_monitoring.service import ADKMonitoringService # NEW
from src.core.adk_monitoring.logging_plugin import LoggingPlugin # NEW
from src.core.adk_monitoring.opentelemetry_plugin import OpenTelemetryMonitoringPlugin # NEW
# Import the new plugins from their correct location
from src.core.adk_monitoring.authorization_plugin import AuthorizationPlugin
from src.core.adk_monitoring.cost_tracking_plugin import CostTrackingPlugin
from src.core.adk_monitoring.dynamic_context_plugin import DynamicContextPlugin
from src.core.adk_monitoring.sanitization_plugin import SanitizationPlugin

logger = logging.getLogger(__name__)

class CommunicationService:
    def __init__(
        self,
        session_service: FirestoreSessionService,
        casefile_service: CasefileService,
        monitoring_service: ADKMonitoringService, # NEW
        logging_plugin: LoggingPlugin, # NEW
        opentelemetry_plugin: OpenTelemetryMonitoringPlugin, # NEW
        authorization_plugin: AuthorizationPlugin, # NEW
        dynamic_context_plugin: DynamicContextPlugin, # NEW
        cost_tracking_plugin: CostTrackingPlugin, # NEW
        sanitization_plugin: SanitizationPlugin, # NEW
    ):
        self.session_service = session_service
        self.casefile_service = casefile_service
        self.monitoring_service = monitoring_service # NEW
        self.plugins = [
            logging_plugin,
            opentelemetry_plugin,
            authorization_plugin,
            dynamic_context_plugin,
            cost_tracking_plugin,
            sanitization_plugin,
        ]
        self.chat_agent = None
        logger.info("CommunicationService initialized.")

    def set_chat_agent(self, chat_agent: Any):
        """Injects the ChatAgent after initialization."""
        self.chat_agent = chat_agent

    async def handle_user_request(self, user_input: str, casefile_id: str, current_user: User) -> Dict[str, Any]:
        """
        Handles an incoming user request, runs the chat agent, and returns the response.
        """
        if not self.chat_agent:
            raise RuntimeError("ChatAgent has not been set in CommunicationService.")

        # Validate casefile existence
        casefile = await self.casefile_service.load_casefile(casefile_id)
        if not casefile:
            raise HTTPException(status_code=404, detail=f"Casefile with ID {casefile_id} not found.")

        session_id = f"chat-{current_user.username}-{casefile_id}"
        app_name = "mds7-rebuild"

        # 1. Haal de sessie op of maak een nieuwe aan
        session = await self.session_service.get_session(app_name, current_user.username, session_id)
        if not session:
            logger.info(f"No existing session '{session_id}', creating new one.")
            # Vul de 'state' met de nodige context voor de agent en tools
            initial_state = {
                "casefile_id": casefile_id,
                "current_user": current_user.model_dump_json()
            }
            session = await self.session_service.create_session(
                app_name=app_name,
                user_id=current_user.username,
                session_id=session_id,
                state=initial_state
            )

        # 2. Initialiseer de ADK Runner
        runner = Runner(
            agent=self.chat_agent,
            session_service=self.session_service,
            app_name=app_name,
            plugins=self.plugins
        )

        # 3. Voer de agent uit met de nieuwe input van de gebruiker
        final_response = "Error: Agent did not produce a final response."
        new_message = genai_types.Content(role='user', parts=[genai_types.Part(text=user_input)])
        
        async for event in runner.run_async(user_id=current_user.username, session_id=session.id, new_message=new_message):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text

        return {"response": final_response, "casefile_id": casefile_id}