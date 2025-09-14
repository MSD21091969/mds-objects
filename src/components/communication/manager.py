# src/components/communication/manager.py

import logging
from typing import Any, Dict, List # MODIFIED

from google.adk.runners import Runner
from google.genai import types as genai_types

from src.core.models.user import User
from src.core.services.firestore_session_service import FirestoreSessionService
from src.components.casefile_management.manager import CasefileManager
from src.core.adk_monitoring.service import ADKMonitoringService # NEW
from src.core.adk_monitoring.plugins.logging_plugin import LoggingPlugin # NEW
from src.core.adk_monitoring.plugins.opentelemetry_plugin import OpenTelemetryMonitoringPlugin # NEW

logger = logging.getLogger(__name__)

class CommunicationManager:
    def __init__(
        self,
        session_service: FirestoreSessionService,
        casefile_manager: CasefileManager,
        monitoring_service: ADKMonitoringService, # NEW
        logging_plugin: LoggingPlugin, # NEW
        opentelemetry_plugin: OpenTelemetryMonitoringPlugin, # NEW
    ):
        self.session_service = session_service
        self.casefile_manager = casefile_manager
        self.monitoring_service = monitoring_service # NEW
        self.logging_plugin = logging_plugin # NEW
        self.opentelemetry_plugin = opentelemetry_plugin # NEW
        self.chat_agent = None
        logger.info("CommunicationManager initialized.")

    def set_chat_agent(self, chat_agent: Any):
        """Injects the ChatAgent after initialization."""
        self.chat_agent = chat_agent

    async def handle_user_request(self, user_input: str, casefile_id: str, current_user: User) -> Dict[str, Any]:
        """
        Handles an incoming user request, runs the chat agent, and returns the response.
        """
        if not self.chat_agent:
            raise RuntimeError("ChatAgent has not been set in CommunicationManager.")

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
            plugins=[self.logging_plugin, self.opentelemetry_plugin] # NEW
        )

        # 3. Voer de agent uit met de nieuwe input van de gebruiker
        final_response = "Error: Agent did not produce a final response."
        new_message = genai_types.Content(role='user', parts=[genai_types.Part(text=user_input)])
        
        async for event in runner.run_async(user_id=current_user.username, session_id=session.id, new_message=new_message):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text

        return {"response": final_response, "casefile_id": casefile_id}