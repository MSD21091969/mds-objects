import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GoogleCalendarEvent, EventDateTime, EventAttendee

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_NAME = 'calendar'
SERVICE_VERSION = 'v3'

class GoogleCalendarService(BaseGoogleService):
    """
    A service class to interact with the Google Calendar API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        super().__init__(client_secrets_path, token_path)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    def list_events(self, calendar_id: str = 'primary', time_min: Optional[datetime] = None, time_max: Optional[datetime] = None, max_results: int = 250) -> List[GoogleCalendarEvent]:
        """
        Lists events from a Google Calendar, handling pagination to retrieve all events in the range.
        """
        if not self.service:
            logger.error("GoogleCalendarService is not authenticated. Cannot list events.")
            return []
        
        all_events = []
        page_token = None
        
        try:
            while True:
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min.isoformat() if time_min else None,
                    timeMax=time_max.isoformat() if time_max else None,
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
            
            logger.info(f"Successfully retrieved {len(all_events)} events from calendar '{calendar_id}'.")
            return all_events

        except HttpError as error:
            logger.error(f"An error occurred while listing events: {error}")
            return []

    def create_event(self, summary: str, start_time: datetime, end_time: datetime, calendar_id: str = 'primary', description: Optional[str] = None, attendees: Optional[List[str]] = None, location: Optional[str] = None) -> Optional[GoogleCalendarEvent]:
        """
        Creates a new event in a Google Calendar.
        """
        if not self.service:
            logger.error("GoogleCalendarService is not authenticated. Cannot create event.")
            return None
        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC', # Assuming UTC for now
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC', # Assuming UTC for now
                },
                'location': location,
                'attendees': [{'email': email} for email in attendees] if attendees else [],
            }
            created_event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            return GoogleCalendarEvent(**created_event)
        except HttpError as error:
            logger.error(f"An error occurred while creating event: {error}")
            return None

    def get_event(self, event_id: str, calendar_id: str = 'primary') -> Optional[GoogleCalendarEvent]:
        """
        Gets a single event from a Google Calendar by its ID.
        """
        if not self.service:
            logger.error("GoogleCalendarService is not authenticated. Cannot get event.")
            return None
        try:
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return GoogleCalendarEvent(**event)
        except HttpError as error:
            logger.error(f"An error occurred while getting event {event_id}: {error}")
            return None

    def update_event(self, event_id: str, calendar_id: str = 'primary', summary: Optional[str] = None, description: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, attendees: Optional[List[str]] = None, location: Optional[str] = None) -> Optional[GoogleCalendarEvent]:
        """
        Updates an existing event in a Google Calendar.
        """
        if not self.service:
            logger.error("GoogleCalendarService is not authenticated. Cannot update event.")
            return None
        try:
            # First, retrieve the event to get its current state
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            # Update fields if provided
            if summary is not None:
                event['summary'] = summary
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            if start_time is not None:
                event['start']['dateTime'] = start_time.isoformat()
            if end_time is not None:
                event['end']['dateTime'] = end_time.isoformat()
            if attendees is not None:
                event['attendees'] = [{'email': email} for email in attendees]

            updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            return GoogleCalendarEvent(**updated_event)
        except HttpError as error:
            logger.error(f"An error occurred while updating event {event_id}: {error}")
            return None

    def delete_event(self, event_id: str, calendar_id: str = 'primary'):
        """
        Deletes an event from a Google Calendar.
        """
        if not self.service:
            logger.error("GoogleCalendarService is not authenticated. Cannot delete event.")
            return
        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(f"Event with ID '{event_id}' deleted successfully.")
        except HttpError as error:
            logger.error(f"An error occurred while deleting event {event_id}: {error}")
