import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types

from src.components.toolsets.google_workspace.calendar.service import GoogleCalendarService

logger = logging.getLogger(__name__)


class GoogleCalendarToolset(BaseToolset):
    """
    A toolset for interacting with Google Calendar.
    """

    def __init__(self, calendar_service: GoogleCalendarService):
        super().__init__()
        self.calendar_service = calendar_service

    async def _list_events(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Lists events from a Google Calendar. Dates must be in ISO 8601 format.
        """
        logger.info(
            f"Toolset is calling calendar_service.list_events for calendar ID: {calendar_id}"
        )

        try:
            time_min_dt = datetime.fromisoformat(time_min) if time_min else None
            time_max_dt = datetime.fromisoformat(time_max) if time_max else None
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        events = self.calendar_service.list_events(
            calendar_id=calendar_id,
            time_min=time_min_dt,
            time_max=time_max_dt,
            max_results=max_results,
        )
        return [event.model_dump() for event in events]

    async def _create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        description: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new event in a Google Calendar. Dates must be in ISO 8601 format.
        """
        logger.info(
            f"Toolset is calling calendar_service.create_event for calendar ID: {calendar_id}, summary: {summary}"
        )

        try:
            start_time_dt = datetime.fromisoformat(start_time)
            end_time_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        event = self.calendar_service.create_event(
            summary=summary,
            start_time=start_time_dt,
            end_time=end_time_dt,
            calendar_id=calendar_id,
            description=description,
            attendees=attendees,
            location=location,
        )
        return event.model_dump() if event else None

    async def _get_event(
        self, event_id: str, calendar_id: str = "primary"
    ) -> Optional[Dict[str, Any]]:
        """
        Gets a single event from a Google Calendar by its ID.
        """
        logger.info(
            f"Toolset is calling calendar_service.get_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )
        event = self.calendar_service.get_event(
            calendar_id=calendar_id, event_id=event_id
        )
        return event.model_dump() if event else None

    async def _update_event(
        self,
        event_id: str,
        calendar_id: str = "primary",
        summary: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        attendees: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Updates an existing event in a Google Calendar. Dates must be in ISO 8601 format.
        """
        logger.info(
            f"Toolset is calling calendar_service.update_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )

        try:
            start_time_dt = datetime.fromisoformat(start_time) if start_time else None
            end_time_dt = datetime.fromisoformat(end_time) if end_time else None
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 date format provided. {e}") from e

        event = self.calendar_service.update_event(
            event_id=event_id,
            calendar_id=calendar_id,
            summary=summary,
            description=description,
            start_time=start_time_dt,
            end_time=end_time_dt,
            attendees=attendees,
            location=location,
        )
        return event.model_dump() if event else None

    async def _delete_event(self, event_id: str, calendar_id: str = "primary") -> None:
        """
        Deletes an event from a Google Calendar.
        """
        logger.info(
            f"Toolset is calling calendar_service.delete_event for calendar ID: {calendar_id}, event ID: {event_id}"
        )
        self.calendar_service.delete_event(calendar_id=calendar_id, event_id=event_id)

    def get_tools(self) -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        event_schema = adk_types.Schema(
            type=adk_types.Type.OBJECT,
            properties={
                "id": adk_types.Schema(type=adk_types.Type.STRING),
                "status": adk_types.Schema(type=adk_types.Type.STRING),
                "summary": adk_types.Schema(type=adk_types.Type.STRING),
                "description": adk_types.Schema(type=adk_types.Type.STRING),
                "location": adk_types.Schema(type=adk_types.Type.STRING),
                "start": adk_types.Schema(
                    type=adk_types.Type.OBJECT,
                    properties={
                        "dateTime": adk_types.Schema(type=adk_types.Type.STRING),
                        "timeZone": adk_types.Schema(type=adk_types.Type.STRING),
                    },
                ),
                "end": adk_types.Schema(
                    type=adk_types.Type.OBJECT,
                    properties={
                        "dateTime": adk_types.Schema(type=adk_types.Type.STRING),
                        "timeZone": adk_types.Schema(type=adk_types.Type.STRING),
                    },
                ),
                "attendees": adk_types.Schema(
                    type=adk_types.Type.ARRAY,
                    items=adk_types.Schema(
                        type=adk_types.Type.OBJECT,
                        properties={
                            "email": adk_types.Schema(type=adk_types.Type.STRING),
                            "displayName": adk_types.Schema(
                                type=adk_types.Type.STRING
                            ),
                            "responseStatus": adk_types.Schema(
                                type=adk_types.Type.STRING
                            ),
                        },
                    ),
                ),
            },
        )

        list_events_declaration = adk_types.FunctionDeclaration(
            name="list_calendar_events",
            description="Lists events from a Google Calendar. Dates must be in ISO 8601 format.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    "calendar_id": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Calendar identifier. Default is 'primary'.",
                    ),
                    "time_min": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Start time in ISO 8601 format, e.g., '2023-10-26T10:00:00Z'.",
                    ),
                    "time_max": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="End time in ISO 8601 format, e.g., '2023-10-26T12:00:00Z'.",
                    ),
                    "max_results": adk_types.Schema(
                        type=adk_types.Type.INTEGER, description="Maximum number of events to return."
                    ),
                },
            ),
            returns=adk_types.Schema(type=adk_types.Type.ARRAY, items=event_schema),
        )

        create_event_declaration = adk_types.FunctionDeclaration(
            name="create_calendar_event",
            description="Creates a new event in a Google Calendar. Dates must be in ISO 8601 format.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    "summary": adk_types.Schema(
                        type=adk_types.Type.STRING, description="Title of the event."
                    ),
                    "start_time": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Start time in ISO 8601 format, e.g., '2023-10-26T10:00:00Z'.",
                    ),
                    "end_time": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="End time in ISO 8601 format, e.g., '2023-10-26T12:00:00Z'.",
                    ),
                    "calendar_id": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Calendar identifier. Default is 'primary'.",
                    ),
                    "description": adk_types.Schema(
                        type=adk_types.Type.STRING, description="Description of the event."
                    ),
                    "attendees": adk_types.Schema(
                        type=adk_types.Type.ARRAY,
                        items=adk_types.Schema(type=adk_types.Type.STRING),
                        description="List of attendee email addresses.",
                    ),
                    "location": adk_types.Schema(
                        type=adk_types.Type.STRING, description="Location of the event."
                    ),
                },
                required=["summary", "start_time", "end_time"],
            ),
            returns=event_schema,
        )

        get_event_declaration = adk_types.FunctionDeclaration(
            name="get_calendar_event",
            description="Gets a single event from a Google Calendar by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    "event_id": adk_types.Schema(
                        type=adk_types.Type.STRING, description="ID of the event to retrieve."
                    ),
                    "calendar_id": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Calendar identifier. Default is 'primary'.",
                    ),
                },
                required=["event_id"],
            ),
            returns=event_schema,
        )

        update_event_declaration = adk_types.FunctionDeclaration(
            name="update_calendar_event",
            description="Updates an existing event in a Google Calendar. Dates must be in ISO 8601 format.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    "event_id": adk_types.Schema(
                        type=adk_types.Type.STRING, description="ID of the event to update."
                    ),
                    "calendar_id": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Calendar identifier. Default is 'primary'.",
                    ),
                    "summary": adk_types.Schema(
                        type=adk_types.Type.STRING, description="New title for the event."
                    ),
                    "description": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="New description for the event.",
                    ),
                    "start_time": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="New start time in ISO 8601 format.",
                    ),
                    "end_time": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="New end time in ISO 8601 format.",
                    ),
                    "attendees": adk_types.Schema(
                        type=adk_types.Type.ARRAY,
                        items=adk_types.Schema(type=adk_types.Type.STRING),
                        description="New list of attendee email addresses.",
                    ),
                    "location": adk_types.Schema(
                        type=adk_types.Type.STRING, description="New location for the event."
                    ),
                },
                required=["event_id"],
            ),
            returns=event_schema,
        )

        delete_event_declaration = adk_types.FunctionDeclaration(
            name="delete_calendar_event",
            description="Deletes an event from a Google Calendar.",
            parameters=adk_types.Schema(
                type=adk_types.Type.OBJECT,
                properties={
                    "event_id": adk_types.Schema(
                        type=adk_types.Type.STRING, description="ID of the event to delete."
                    ),
                    "calendar_id": adk_types.Schema(
                        type=adk_types.Type.STRING,
                        description="Calendar identifier. Default is 'primary'.",
                    ),
                },
                required=["event_id"],
            ),
        )

        return [
            FunctionTool(func=self._list_events, declaration=list_events_declaration),
            FunctionTool(func=self._create_event, declaration=create_event_declaration),
            FunctionTool(func=self._get_event, declaration=get_event_declaration),
            FunctionTool(func=self._update_event, declaration=update_event_declaration),
            FunctionTool(func=self._delete_event, declaration=delete_event_declaration),
        ]
