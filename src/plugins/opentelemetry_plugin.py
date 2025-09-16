import logging
from typing import Any, Dict, Optional

from google.adk.plugins import BasePlugin
from google.adk.events import Event
from google.adk.agents import Agent
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
        self.tool_spans: Dict[str, trace.Span] = {}
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
            # Use add_event for lightweight event logging on the main span,
            # instead of creating a noisy child span for every event.
            self.current_run_span.add_event(
                name=f"adk.event.{event.type}",
                attributes={
                    "adk.event.content_summary": str(event.content)[:250]
                },
                timestamp=int(event.timestamp.timestamp() * 1e9) # OTel expects nanoseconds
            )
            logger.debug(f"Added OpenTelemetry event: {event.type} for session {session.id}")

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

    async def on_tool_start(self, session: Session, agent: Agent, tool: Any, **kwargs: Any) -> None:
        if self.current_run_span:
            tool_args = kwargs.get("tool_args", {})
            tool_span = self.tracer.start_span(
                f"adk.tool.{tool.name}",
                parent=self.current_run_span,
                attributes={
                    "adk.session_id": session.id,
                    "adk.agent_name": agent.name,
                    "adk.tool.name": tool.name,
                    "adk.tool.args": str(tool_args),
                }
            )
            # Use a unique key for the tool call, e.g., combining session and tool name
            span_key = f"{session.id}-{tool.name}"
            self.tool_spans[span_key] = tool_span
            logger.debug(f"Started OpenTelemetry span for tool: {tool.name}")

    async def on_tool_end(self, session: Session, agent: Agent, tool: Any, result: Any, **kwargs: Any) -> None:
        span_key = f"{session.id}-{tool.name}"
        if span_key in self.tool_spans:
            tool_span = self.tool_spans.pop(span_key)
            tool_span.set_attribute("adk.tool.result", str(result)[:500]) # Truncate long results
            tool_span.set_status(trace.Status(trace.StatusCode.OK))
            tool_span.end()
            logger.debug(f"Ended OpenTelemetry span for successful tool: {tool.name}")

    async def on_tool_error(self, session: Session, agent: Agent, tool: Any, error: Exception, **kwargs: Any) -> None:
        span_key = f"{session.id}-{tool.name}"
        if span_key in self.tool_spans:
            tool_span = self.tool_spans.pop(span_key)
            tool_span.set_status(trace.Status(trace.StatusCode.ERROR, description=str(error)))
            tool_span.record_exception(error)
            tool_span.end()
            logger.error(f"Ended OpenTelemetry span for failed tool: {tool.name}")
