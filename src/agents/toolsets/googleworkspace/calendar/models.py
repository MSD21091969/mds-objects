# src/components/toolsets/google_workspace/calendar/updated_models.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class EventDateTime(BaseModel):
    # 'dateTime' is nu van het type datetime voor betere verwerking en validatie
    dateTime: datetime
    timeZone: Optional[str] = None # Timezone kan soms ontbreken

class EventAttendee(BaseModel):
    email: str
    responseStatus: str
    optional: Optional[bool] = None

class CalendarEvent(BaseModel):
    """Vertegenwoordigt een Google Calendar-gebeurtenis, robuust voor ontbrekende velden."""
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start: Optional[EventDateTime] = None
    end: Optional[EventDateTime] = None
    status: Optional[str] = None
    attendees: Optional[List[EventAttendee]] = None
    htmlLink: Optional[str] = None

    class Config:
        extra = 'ignore' # Negeer velden die niet in het model zijn gedefinieerd

class EventList(BaseModel):
    """Een lijst van agenda-evenementen met bijbehorende metadata van de API."""
    kind: str
    etag: str
    nextPageToken: Optional[str] = None
    items: List[CalendarEvent] = []

class ListEventsQuery(BaseModel):
    """Input validatie voor de list_events tool."""
    calendar_id: str = Field("primary", description="De ID van de agenda om op te vragen. 'primary' is de standaard.")
    # De velden voor tijd zijn nu optioneel om flexibeler te zijn
    time_min: Optional[str] = Field(None, description="Start van het tijdsvenster in ISO 8601-formaat.")
    time_max: Optional[str] = Field(None, description="Einde van het tijdsvenster in ISO 8601-formaat.")
    max_results: int = Field(10, description="Maximaal aantal evenementen om terug te geven.")