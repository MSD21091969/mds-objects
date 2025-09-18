import logging
from typing import List, Dict, Any, Optional, Union

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GooglePerson, Name, EmailAddress, PhoneNumber
from src.core.managers.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/contacts']
SERVICE_NAME = 'people'
SERVICE_VERSION = 'v1'

class GooglePeopleService(BaseGoogleService):
    """
    A service class to interact with the Google People API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.scopes = SCOPES

    async def list_contacts(self, user_id: str, page_size: int = 100) -> List[GooglePerson]:
        """
        Lists contacts from the user's Google Contacts.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated People service for user {user_id}.")
            return []
        try:
            results = self.service.people().connections().list(
                resourceName='people/me',
                pageSize=page_size,
                personFields='names,emailAddresses,phoneNumbers,photos'
            ).execute()
            connections = results.get('connections', [])
            logger.info(f"Retrieved {len(connections)} contacts for user '{user_id}'.")
            return [GooglePerson(**person_data) for person_data in connections]
        except HttpError as error:
            logger.error(f"An error occurred while listing contacts for user '{user_id}': {error}")
            return []

    async def get_contact(self, user_id: str, resource_name: str) -> Optional[GooglePerson]:
        """
        Gets a single contact by its resource name.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated People service for user {user_id}.")
            return None
        try:
            person = self.service.people().get(
                resourceName=resource_name,
                personFields='names,emailAddresses,phoneNumbers,photos'
            ).execute()
            logger.info(f"Retrieved contact '{resource_name}' for user '{user_id}'.")
            return GooglePerson(**person)
        except HttpError as error:
            logger.error(f"An error occurred while getting contact '{resource_name}' for user '{user_id}': {error}")
            return None

    async def create_contact(self, user_id: str, given_name: str, family_name: str, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[GooglePerson]:
        """
        Creates a new contact.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated People service for user {user_id}.")
            return None
        try:
            new_contact = {
                'names': [{'givenName': given_name, 'familyName': family_name}],
                'emailAddresses': [{'value': email}] if email else [],
                'phoneNumbers': [{'value': phone}] if phone else [],
            }
            created_person = self.service.people().createContact(body=new_contact).execute()
            logger.info(f"Created contact '{given_name} {family_name}' for user '{user_id}'.")
            return GooglePerson(**created_person)
        except HttpError as error:
            logger.error(f"An error occurred while creating contact for user '{user_id}': {error}")
            return None

    async def update_contact(self, user_id: str, resource_name: str, etag: str, updates: Dict[str, Union[str, None]]) -> Optional[GooglePerson]:
        """
        Updates an existing contact.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated People service for user {user_id}.")
            return None
        try:
            given_name = updates.get('given_name')
            family_name = updates.get('family_name')
            email = updates.get('email')
            phone = updates.get('phone')

            # Build the update body
            update_body = {
                'etag': etag,
            }
            
            # Only update fields that are provided
            update_person_fields = []
            if given_name or family_name:
                update_person_fields.append('names')
                update_body['names'] = [{'givenName': given_name, 'familyName': family_name}]
            if email:
                update_person_fields.append('emailAddresses')
                update_body['emailAddresses'] = [{'value': email}]
            if phone:
                update_person_fields.append('phoneNumbers')
                update_body['phoneNumbers'] = [{'value': phone}]

            if not update_person_fields:
                logger.warning("Update contact called with no fields to update.")
                return await self.get_contact(user_id, resource_name)

            updated_person = self.service.people().updateContact(
                resourceName=resource_name,
                updatePersonFields=','.join(update_person_fields),
                body=update_body
            ).execute()
            logger.info(f"Updated contact '{resource_name}' for user '{user_id}'.")
            return GooglePerson(**updated_person)
        except HttpError as error:
            logger.error(f"An error occurred while updating contact '{resource_name}' for user '{user_id}': {error}")
            return None

    async def delete_contact(self, user_id: str, resource_name: str) -> bool:
        """
        Deletes a contact.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated People service for user {user_id}.")
            return False
        try:
            self.service.people().deleteContact(resourceName=resource_name).execute()
            logger.info(f"Contact '{resource_name}' deleted successfully for user '{user_id}'.")
            return True
        except HttpError as error:
            logger.error(f"An error occurred while deleting contact '{resource_name}' for user '{user_id}': {error}")
            return False