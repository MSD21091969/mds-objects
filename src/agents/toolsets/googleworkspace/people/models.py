# src/components/toolsets/google_workspace/people/models.py

from pydantic import BaseModel, Field
from typing import List, Optional

class Name(BaseModel):
    displayName: str
    
class EmailAddress(BaseModel):
    value: str
    
class PhoneNumber(BaseModel):
    value: str
    formattedType: Optional[str] = None

class Address(BaseModel):
    formattedValue: str
    
class Organization(BaseModel):
    name: str
    title: Optional[str] = None
    
class Person(BaseModel):
    """Represents a Google People API person resource."""
    resourceName: str
    etag: str
    names: Optional[List[Name]] = None
    emailAddresses: Optional[List[EmailAddress]] = None
    phoneNumbers: Optional[List[PhoneNumber]] = None
    addresses: Optional[List[Address]] = None
    organizations: Optional[List[Organization]] = None
    
    class Config:
        extra = 'ignore'
        
class SearchContactsResponse(BaseModel):
    results: Optional[List[Person]] = None
    nextPageToken: Optional[str] = None

class SearchContactsQuery(BaseModel):
    """Input validation for the search_contacts tool."""
    query: str = Field(..., description="The query to search for contacts.")
    read_mask: str = Field(
        "names,emailAddresses,phoneNumbers,addresses,organizations", 
        description="Comma-separated list of fields to return."
    )
    page_token: Optional[str] = Field(None, description="The next page token, if paginating through results.")