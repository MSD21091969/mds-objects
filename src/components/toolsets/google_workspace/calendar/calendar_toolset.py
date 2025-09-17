import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from typing import List, Dict, Any
from datetime import datetime

from src.components.toolsets.google_workspace.calendar.service import GoogleCalendarService
from src.components.toolsets.google_workspace.calendar.models import CalendarEvent

logger = logging.getLogger(__name__)

class CalendarToolset(BaseToolset):
    """A toolset for interacting with Google Calendar."""

    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.calendar_service = GoogleCalendarService(client_secrets_path, token_path)
        super().__init__()

    def _list_events(self, time_min: str, time_max: str, max_results: int = 10) -> str:
        """Lists events on the user's primary calendar within a specified time range (ISO 8601 format)."""
        try:
            events = self.calendar_service.list_events(time_min, time_max, max_results)
            return "\n".join([event.json() for event in events])
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return f"Error listing calendar events: {e}"

    def _create_event(self, summary: str, description: str, start_time: str, end_time: str, time_zone: str = "UTC") -> str:
        """Creates a new event on the user's primary calendar."""
        try:
            event = self.calendar_service.create_event(summary, description, start_time, end_time, time_zone)
            return event.json() if event else "Failed to create event."
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return f"Error creating calendar event: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        list_events_declaration = adk_types.FunctionDeclaration(
            name="list_calendar_events",
            description="Lists events on the user's primary calendar within a specified time range (ISO 8601 format).",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "time_min": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The start time for the events in ISO 8601 format (e.g., '2023-10-27T10:00:00Z').",
                    ),
                    "time_max": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The end time for the events in ISO 8601 format (e.g., '2023-10-27T11:00:00Z').",
                    ),
                    "max_results": adk_types.Schema(
                        type=adk_types.SchemaType.INTEGER,
                        description="The maximum number of events to return.",
                        default=10
                    ),
                },
                required=["time_min", "time_max"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing a list of matching calendar events.",
            ),
        )

        create_event_declaration = adk_types.FunctionDeclaration(
            name="create_calendar_event",
            description="Creates a new event on the user's primary calendar.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "summary": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="Summary of the event.",
                    ),
                    "description": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="Description of the event.",
                    ),
                    "start_time": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="Start time of the event in ISO 8601 format (e.g., '2023-10-27T10:00:00Z').",
                    ),
                    "end_time": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="End time of the event in ISO 8601 format (e.g., '2023-10-27T11:00:00Z').",
                    ),
                    "time_zone": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="Time zone for the event (e.g., 'America/Los_Angeles'). Defaults to UTC.",
                        default="UTC"
                    ),
                },
                required=["summary", "description", "start_time", "end_time"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A JSON string containing the created event details, or 'Failed to create event.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._list_events,
                declaration=list_events_declaration,
            ),
            FunctionTool(
                func=self._create_event,
                declaration=create_event_declaration,
            ),
        ]
