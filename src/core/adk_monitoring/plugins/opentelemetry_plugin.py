import logging
from typing import Any, Dict, Optional

from google.adk.plugins import BasePlugin
from google.adk.events import Event
from google.adk.sessions import Session

from opentelemetry import trace

from src.core.adk_monitoring.service import ADKMonitoringService

logger = logging.getLogger(__name__)

class OpenTelemetryMonitoringPlugin(BasePlugin):
    """
    An ADK plugin that integrates with OpenTelemetry for tracing agent runs.
    It also uses ADKMonitoringService for logging span lifecycle.
    """
    def __init__(self, monitoring_service: ADKMonitoringService, app_name: str):
        self.monitoring_service = monitoring_service
        self.tracer = trace.get_tracer(app_name)
        self.current_run_span: Optional[trace.Span] = None
        logger.info("OpenTelemetryMonitoringPlugin initialized.")

    async def on_run_start(self, session: Session, **kwargs: Any) -> None:
        self.current_run_span = self.tracer.start_span(
            f"adk.agent.run.{session.id}",
            attributes={
                "adk.session_id": session.id,
                "adk.user_id": session.user_id,
                "adk.app_name": session.app_name,
                "adk.run_type": "chat_agent",
            }
        )
        self.monitoring_service.log_event(
            "opentelemetry_span_start",
            {"span_name": f"adk.agent.run.{session.id}", "session_id": session.id}
        )
        logger.debug(f"Started OpenTelemetry span for ADK run: {session.id}")

    async def on_event(self, session: Session, event: Event, **kwargs: Any) -> None:
        if self.current_run_span:
            with self.tracer.start_as_current_span(
                f"adk.event.{event.type}",
                parent=self.current_run_span,
                attributes={
                    "adk.event.type": event.type,
                    "adk.event.timestamp": event.timestamp.isoformat(),
                    "adk.session_id": session.id,
                    "adk.event.content_summary": str(event.content)[:250], # Log summary to avoid large payloads
                }
            ) as event_span:
                self.monitoring_service.log_event(
                    "opentelemetry_event_span",
                    {"event_type": event.type, "session_id": session.id}
                )
                logger.debug(f"Processed ADK event: {event.type} for session {session.id}")

    async def on_run_end(self, session: Session, **kwargs: Any) -> None:
        if self.current_run_span:
            self.current_run_span.end()
            self.monitoring_service.log_event(
                "opentelemetry_span_end",
                {"span_name": f"adk.agent.run.{session.id}", "session_id": session.id, "status": "success"}
            )
            logger.debug(f"Ended OpenTelemetry span for ADK run: {session.id}")

    async def on_run_error(self, session: Session, error: Exception, **kwargs: Any) -> None:
        if self.current_run_span:
            self.current_run_span.set_status(trace.Status(trace.StatusCode.ERROR, description=str(error)))
            self.current_run_span.record_exception(error)
            self.current_run_span.end()
            self.monitoring_service.log_event(
                "opentelemetry_span_end",
                {"span_name": f"adk.agent.run.{session.id}", "session_id": session.id, "status": "error", "error_message": str(error)}
            )
            logger.error(f"ADK run for session {session.id} ended with error: {error}")
