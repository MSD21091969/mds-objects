# src/components/toolsets/google_workspace/calendar/google_calendar_toolset.py

import logging
from typing import Optional
from datetime import datetime

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, ReadonlyContext
from google.adk.tools.base_tool import BaseTool, Parameter

from .service import CalendarService
from .models import ListEventsQuery

logger = logging.getLogger(__name__)

class CalendarToolset(BaseToolset):
    """Exposes methods from the CalendarService as ADK Tools."""
    def __init__(self, calendar_service: CalendarService):
        self.calendar_service = calendar_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        
        async def _list_events_tool(
            calendar_id: str,
            time_min: Optional[str] = None,
            time_max: Optional[str] = None,
            max_results: Optional[int] = 10,
            tool_context: ToolContext = None
        ) -> dict:
            """
            This tool retrieves a list of events from a user's Google Calendar.
            It is ideal for answering questions about upcoming meetings, appointments,
            and availability.
            """
            user_id = tool_context.invocation_context.session.user_id
            
            # Use the Pydantic model to validate the input from the agent
            validated_query = ListEventsQuery(
                calendar_id=calendar_id,
                time_min=time_min,
                time_max=time_max,
                max_results=max_results
            )
            
            # Pass the validated Pydantic model object directly to the service
            return await self.calendar_service.list_events(user_id=user_id, query=validated_query)

        tools = [
            FunctionTool(
                func=_list_events_tool,
                name="calendar_list_events",
                description="Retrieves events from the user's Google Calendar to answer questions about meetings, appointments, and availability.",
                parameters=[
                    Parameter(
                        name="calendar_id",
                        type=str,
                        description="The ID of the calendar to query. Use 'primary' for the user's main calendar unless another ID is specified.",
                        required=True
                    ),
                    Parameter(
                        name="time_min",
                        type=str,
                        description="The start time of the time window for the events, in ISO 8601 format (e.g., '2023-10-27T10:00:00Z'). This parameter is optional.",
                        required=False
                    ),
                    Parameter(
                        name="time_max",
                        type=str,
                        description="The end time of the time window for the events, in ISO 8601 format (e.g., '2023-10-28T10:00:00Z'). This parameter is optional.",
                        required=False
                    ),
                    Parameter(
                        name="max_results",
                        type=int,
                        description="The maximum number of events to return. The default is 10.",
                        required=False
                    )
                ]
            )
        ]
        return tools