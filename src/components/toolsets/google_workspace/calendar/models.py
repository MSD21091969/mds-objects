# MDSAPP/core/models/google/calendar.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class EventDateTime(BaseModel):
    """
    Represents a date or date-time value for an event.
    """
    date_time: Optional[str] = Field(None, alias='dateTime')
    date: Optional[str] = None # For all-day events
    time_zone: Optional[str] = Field(None, alias='timeZone')

    model_config = ConfigDict(populate_by_name=True)

class EventAttendee(BaseModel):
    """
    Represents an attendee of an event.
    """
    email: str
    display_name: Optional[str] = Field(None, alias='displayName')
    response_status: Optional[str] = Field(None, alias='responseStatus')

    model_config = ConfigDict(populate_by_name=True)

class GoogleCalendarEvent(BaseModel):
    """
    Represents a Google Calendar Event resource.
    """
    id: str
    status: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: EventDateTime
    end: EventDateTime
    html_link: Optional[str] = Field(None, alias='htmlLink')
    attendees: Optional[List[EventAttendee]] = Field(default_factory=list)
    creator: Optional[Dict[str, Any]] = None
    organizer: Optional[Dict[str, Any]] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    # Add more fields as needed, e.g., status, creator, organizer, etc.

    model_config = ConfigDict(populate_by_name=True)
