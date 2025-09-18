# src/components/toolsets/google_workspace/calendar/service.py

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from src.core.managers.database_manager import DatabaseManager
from .models import GoogleCalendarEvent

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar'] # Use read/write scope for full functionality
SERVICE_NAME = 'calendar'
SERVICE_VERSION = 'v3'

class GoogleCalendarService(BaseGoogleService):
    """
    A service class to interact with the Google Calendar API using user-specific credentials.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.scopes = SCOPES

    async def list_events(
        self, 
        user_id: str,
        calendar_id: str = 'primary', 
        time_min: Optional[datetime] = None, 
        time_max: Optional[datetime] = None, 
        max_results: int = 250
    ) -> List[GoogleCalendarEvent]:
        """
        Lists events from a user's Google Calendar, handling pagination.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Calendar service for user {user_id}.")
            return []
        
        all_events = []
        page_token = None
        
        try:
            while True:
                events_result = service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min.isoformat() + 'Z' if time_min else None,
                    timeMax=time_max.isoformat() + 'Z' if time_max else None,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime',
                    pageToken=page_token
                ).execute()
                
                events = events_result.get('items', [])
                for event_data in events:
                    try:
                        all_events.append(GoogleCalendarEvent(**event_data))
                    except Exception as e:
                        logger.warning(f"Could not parse event with ID {event_data.get('id')}. Error: {e}")
                
                page_token = events_result.get('nextPageToken')
                if not page_token:
                    break
            
            logger.info(f"Successfully retrieved {len(all_events)} events from calendar '{calendar_id}' for user '{user_id}'.")
            return all_events

        except HttpError as error:
            logger.error(f"An error occurred while listing events for user {user_id}: {error}")
            # Depending on the error (e.g., 401/403), you might want to invalidate the user's token.
            return []

    async def create_event(
        self, 
        user_id: str,
        summary: str, 
        start_time: datetime, 
        end_time: datetime, 
        calendar_id: str = 'primary', 
        description: Optional[str] = None, 
        attendees: Optional[List[str]] = None, 
        location: Optional[str] = None
    ) -> Optional[GoogleCalendarEvent]:
        """
        Creates a new event in a Google Calendar.
        Note: Requires 'https://www.googleapis.com/auth/calendar' scope.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Calendar service for user {user_id}.")
            return None
        try:
            event_body = {
                'summary': summary,
                'description': description,
                'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
                'location': location,
                'attendees': [{'email': email} for email in attendees] if attendees else [],
            }
            created_event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
            logger.info(f"Successfully created event '{summary}' for user '{user_id}'.")
            return GoogleCalendarEvent(**created_event)
        except HttpError as error:
            logger.error(f"An error occurred while creating event for user {user_id}: {error}")
            return None

    async def get_event(
        self, 
        user_id: str,
        event_id: str, 
        calendar_id: str = 'primary'
    ) -> Optional[GoogleCalendarEvent]:
        """
        Gets a single event from a Google Calendar by its ID.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Calendar service for user {user_id}.")
            return None
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return GoogleCalendarEvent(**event)
        except HttpError as error:
            logger.error(f"An error occurred while getting event {event_id} for user {user_id}: {error}")
            return None

    # Update and Delete methods would follow a similar pattern, always passing `user_id`.