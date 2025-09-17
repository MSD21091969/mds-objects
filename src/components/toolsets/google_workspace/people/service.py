import logging
from typing import List, Dict, Any, Optional

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GooglePerson, Name, EmailAddress, PhoneNumber

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/contacts']
SERVICE_NAME = 'people'
SERVICE_VERSION = 'v1'

class GooglePeopleService(BaseGoogleService):
    """
    A service class to interact with the Google People API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        super().__init__(client_secrets_path, token_path)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    def list_contacts(self, page_size: int = 100) -> List[GooglePerson]:
        """
        Lists contacts from the user's Google Contacts.
        """
        if not self.service:
            logger.error("GooglePeopleService is not authenticated. Cannot list contacts.")
            return []
        try:
            results = self.service.people().connections().list(
                resourceName='people/me',
                pageSize=page_size,
                personFields='names,emailAddresses,phoneNumbers,photos'
            ).execute()
            connections = results.get('connections', [])
            return [GooglePerson(**person_data) for person_data in connections]
        except HttpError as error:
            logger.error(f"An error occurred while listing contacts: {error}")
            return []

    def get_contact(self, resource_name: str) -> Optional[GooglePerson]:
        """
        Gets a single contact by its resource name.
        """
        if not self.service:
            logger.error("GooglePeopleService is not authenticated. Cannot get contact.")
            return None
        try:
            person = self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,photos'
            ).execute()
            return GooglePerson(**person)
        except HttpError as error:
            logger.error(f"An error occurred while getting contact {resource_name}: {error}")
            return None

    def create_contact(self, given_name: str, family_name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[GooglePerson]:
        """
        Creates a new contact.
        """
        if not self.service:
            logger.error("GooglePeopleService is not authenticated. Cannot create contact.")
            return None
        try:
            new_contact = {
                'names': [{'givenName': given_name, 'familyName': family_name}],
                'emailAddresses': [{'value': email}] if email else [],
                'phoneNumbers': [{'value': phone}] if phone else [],
            }
            created_person = self.service.people().createContact(body=new_contact).execute()
            return GooglePerson(**created_person)
        except HttpError as error:
            logger.error(f"An error occurred while creating contact: {error}")
            return None

    def update_contact(self, resource_name: str, etag: str, given_name: Optional[str] = None, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[GooglePerson]:
        """
        Updates an existing contact.
        """
        if not self.service:
            logger.error("GooglePeopleService is not authenticated. Cannot update contact.")
            return None
        try:
            # Build the update body
            update_body = {
                'etag': etag,
                'names': [{'givenName': given_name, 'familyName': family_name}] if given_name or family_name else [],
                'emailAddresses': [{'value': email}] if email else [],
                'phoneNumbers': [{'value': phone}] if phone else [],
            }
            
            # Only update fields that are provided
            update_person_fields = []
            if given_name or family_name:
                update_person_fields.append('names')
            if email:
                update_person_fields.append('emailAddresses')
            if phone:
                update_person_fields.append('phoneNumbers')

            updated_person = self.service.people().updateContact(
                resourceName=resource_name,
                updatePersonFields=','.join(update_person_fields),
                body=update_body
            ).execute()
            return GooglePerson(**updated_person)
        except HttpError as error:
            logger.error(f"An error occurred while updating contact {resource_name}: {error}")
            return None

    def delete_contact(self, resource_name: str):
        """
        Deletes a contact.
        """
        if not self.service:
            logger.error("GooglePeopleService is not authenticated. Cannot delete contact.")
            return
        try:
            self.service.people().deleteContact(resourceName=resource_name).execute()
            logger.info(f"Contact {resource_name} deleted successfully.")
        except HttpError as error:
            logger.error(f"An error occurred while deleting contact {resource_name}: {error}")