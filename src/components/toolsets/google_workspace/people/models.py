# MDSAPP/core/models/google/people.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class Name(BaseModel):
    """
    Represents a person's name.
    """
    display_name: Optional[str] = Field(None, alias='displayName')
    family_name: Optional[str] = Field(None, alias='familyName')
    given_name: Optional[str] = Field(None, alias='givenName')

    model_config = ConfigDict(populate_by_name=True)

class EmailAddress(BaseModel):
    """
    Represents a person's email address.
    """
    value: str
    type: Optional[str] = None # e.g., "home", "work"

    model_config = ConfigDict(populate_by_name=True)

class PhoneNumber(BaseModel):
    """
    Represents a person's phone number.
    """
    value: str
    type: Optional[str] = None # e.g., "home", "work", "mobile"

    model_config = ConfigDict(populate_by_name=True)

class Photo(BaseModel):
    """
    Represents a person's photo.
    """
    url: str

    model_config = ConfigDict(populate_by_name=True)

class GooglePerson(BaseModel):
    """
    Represents a Google People API Person resource.
    """
    resource_name: str = Field(..., alias='resourceName')
    etag: str
    names: Optional[List[Name]] = None
    email_addresses: Optional[List[EmailAddress]] = Field(None, alias='emailAddresses')
    phone_numbers: Optional[List[PhoneNumber]] = Field(None, alias='phoneNumbers')
    photos: Optional[List[Photo]] = Field(None, alias='photos')
    # Add more fields as needed, e.g., organizations, addresses, birthdays, etc.

    model_config = ConfigDict(populate_by_name=True)
