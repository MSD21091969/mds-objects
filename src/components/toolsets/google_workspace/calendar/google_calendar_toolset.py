import logging
from typing import Optional, List
from datetime import datetime

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.components.toolsets.google_workspace.calendar.service import GoogleCalendarService
from src.components.toolsets.google_workspace.calendar.models import GoogleCalendarEvent

logger = logging.getLogger(__name__)


class GoogleCalendarToolset(BaseToolset):
    """
    A toolset for interacting with Google Calendar.
    """

    def __init__(self, calendar_service: GoogleCalendarService):
        super().__init__()
        self.calendar_service = calendar_service

    async def list_events(
        self,
        tool_context: ToolContext,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
    ) -> List[GoogleCalendarEvent]:
        """
        Lists events from a Google Calendar. Dates must be in ISO 8601 format.
        Args:
            tool_context: The runtime context provided by the ADK.
            calendar_id: The ID of the calendar to list events from. Defaults to 'primary'.
            time_min: The start of the time range to query, in ISO 8601 format.
            time_max: The end of the time range to query, in ISO 8601 format.
            max_results: The maximum number of events to return.
        """
        logger.info(
            f"Toolset is calling calendar_service.list_events for calendar ID: {calendar_id}"
        )

        try:
            time_min_dt = datetime.fromisoformat(time_min) if time_min else None
            time_max_dt = datetime.fromisoformat(time_max) if time_max else None
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        return await self.calendar_service.list_events(
            calendar_id=calendar_id,
            time_min=time_min_dt,
            time_max=time_max_dt,
            max_results=max_results,
        )

    async def create_event(
        self,
        tool_context: ToolContext,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Optional[GoogleCalendarEvent]:
        """
        Creates a new event in a Google Calendar. Dates must be in ISO 8601 format.
        Args:
            tool_context: The runtime context provided by the ADK.
            summary: The title of the event.
            start_time: The start time of the event in ISO 8601 format.
            end_time: The end time of the event in ISO 8601 format.
            calendar_id: The ID of the calendar to create the event in. Defaults to 'primary'.
            description: A description of the event.
            attendees: A list of email addresses of attendees.
            location: The location of the event.
        """
        logger.info(
            f"Toolset is calling calendar_service.create_event for calendar ID: {calendar_id}, summary: {summary}"
        )

        try:
            start_time_dt = datetime.fromisoformat(start_time)
            end_time_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        return await self.calendar_service.create_event(
            summary=summary,
            start_time=start_time_dt,
            end_time=end_time_dt,
            calendar_id=calendar_id,
            description=description,
            attendees=attendees,
            location=location,
        )

    async def get_event(
        self, tool_context: ToolContext, event_id: str, calendar_id: str = "primary"
    ) -> Optional[GoogleCalendarEvent]:
        """
        Gets a single event from a Google Calendar by its ID.
        Args:
            tool_context: The runtime context provided by the ADK.
            event_id: The ID of the event to retrieve.
            calendar_id: The ID of the calendar the event belongs to. Defaults to 'primary'.
        """
        logger.info(
            f"Toolset is calling calendar_service.get_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )
        return await self.calendar_service.get_event(
            calendar_id=calendar_id, event_id=event_id
        )

    async def update_event(
        self,
        tool_context: ToolContext,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Optional[GoogleCalendarEvent]:
        """
        Updates an existing event in a Google Calendar. Dates must be in ISO 8601 format.
        Args:
            tool_context: The runtime context provided by the ADK.
            event_id: The ID of the event to update.
            calendar_id: The ID of the calendar the event belongs to. Defaults to 'primary'.
            summary: The new title for the event.
            description: The new description for the event.
            start_time: The new start time in ISO 8601 format.
            end_time: The new end time in ISO 8601 format.
            attendees: A new list of attendee email addresses.
            location: The new location for the event.
        """
        logger.info(
            f"Toolset is calling calendar_service.update_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )

        try:
            start_time_dt = datetime.fromisoformat(start_time) if start_time else None
            end_time_dt = datetime.fromisoformat(end_time) if end_time else None
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        return await self.calendar_service.update_event(
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            start_time=start_time_dt,
            end_time=end_time_dt,
            attendees=attendees,
            location=location,
        )

    async def delete_event(
        self, tool_context: ToolContext, event_id: str, calendar_id: str = "primary"
    ) -> bool:
        """
        Deletes an event from a Google Calendar. Returns True on success.
        Args:
            tool_context: The runtime context provided by the ADK.
            event_id: The ID of the event to delete.
            calendar_id: The ID of the calendar the event belongs to. Defaults to 'primary'.
        """
        logger.info(
            f"Toolset is calling calendar_service.delete_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )
        await self.calendar_service.delete_event(calendar_id=calendar_id, event_id=event_id)
        return True

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        return [
            FunctionTool(func=self.list_events),
            FunctionTool(func=self.create_event),
            FunctionTool(func=self.get_event),
            FunctionTool(func=self.update_event),
            FunctionTool(func=self.delete_event),
        ]
