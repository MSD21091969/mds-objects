# src/components/toolsets/google_workspace/docs/service.py

import logging
from typing import Optional

from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from src.core.managers.database_manager import DatabaseManager
from .models import GoogleDoc

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/documents']
SERVICE_NAME = 'docs'
SERVICE_VERSION = 'v1'

class GoogleDocsService(BaseGoogleService):
    """
    A service class to interact with the Google Docs API using user-specific credentials.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
        self.service_name = SERVICE_NAME
        self.service_version = SERVICE_VERSION
        self.scopes = SCOPES

    async def create_document(
        self,
        user_id: str,
        title: str,
        body_content: Optional[str] = None
    ) -> Optional[GoogleDoc]:
        """
        Creates a new Google Doc for a specific user.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Docs service for user {user_id}.")
            return None

        try:
            document_body = {'title': title}
            doc = service.documents().create(body=document_body).execute()
            doc_id = doc.get('documentId')

            if body_content:
                requests = [{
                    'insertText': {
                        'location': {'index': 1},
                        'text': body_content
                    }
                }]
                service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()

            # Fetch the full document again to get all properties
            created_doc = service.documents().get(documentId=doc_id).execute()
            logger.info(f"Successfully created Google Doc '{title}' for user '{user_id}'.")
            return GoogleDoc(**created_doc)

        except HttpError as error:
            logger.error(f"An error occurred while creating document for user {user_id}: {error}")
            return None

    async def get_document(self, user_id: str, document_id: str) -> Optional[GoogleDoc]:
        """
        Gets a Google Doc by its ID for a specific user.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Docs service for user {user_id}.")
            return None
        try:
            doc = service.documents().get(documentId=document_id).execute()
            return GoogleDoc(**doc)
        except HttpError as error:
            logger.error(f"An error occurred while getting document {document_id} for user {user_id}: {error}")
            return None

    async def update_document_body(
        self,
        user_id: str,
        document_id: str,
        body_content: str
    ) -> Optional[GoogleDoc]:
        """
        Replaces the entire body of a Google Doc with new content for a specific user.
        """
        service = await self.get_service_for_user(user_id)
        if not service:
            logger.error(f"Could not get authenticated Google Docs service for user {user_id}.")
            return None
        try:
            # Get current document size to delete existing content
            document = service.documents().get(documentId=document_id, fields='body(content)').execute()
            content = document.get('body', {}).get('content', [])
            
            requests = []
            if content:
                end_index = content[-1].get('endIndex')
                if end_index and end_index > 1:
                    requests.append({'deleteContentRange': {'range': {'startIndex': 1, 'endIndex': end_index - 1}}})

            if body_content:
                requests.append({'insertText': {'location': {'index': 1}, 'text': body_content}})

            if requests:
                service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
            
            return await self.get_document(user_id, document_id)

        except HttpError as error:
            logger.error(f"An error occurred while updating document {document_id} for user {user_id}: {error}")
            return None