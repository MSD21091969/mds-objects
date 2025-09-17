import logging
from typing import Optional
from googleapiclient.errors import HttpError

from src.components.toolsets.google_workspace.base_service import BaseGoogleService
from .models import GoogleDoc

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/documents']
SERVICE_NAME = 'docs'
SERVICE_VERSION = 'v1'

class GoogleDocsService(BaseGoogleService):
    """
    A service class to interact with the Google Docs API, inheriting common logic
    from BaseGoogleService.
    """
    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        super().__init__(client_secrets_path, token_path)
        self._build_service(SERVICE_NAME, SERVICE_VERSION, SCOPES)

    def create_document(self, title: str, body_content: str) -> Optional[GoogleDoc]:
        """
        Creates a new Google Doc.
        """
        if not self.service:
            logger.error("GoogleDocsService is not authenticated.")
            return None

        try:
            document = {
                'title': title
            }
            doc = self.service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')

            if body_content:
                requests = [
                    {
                        'insertText': {
                            'location': {
                                'index': 1,
                            },
                            'text': body_content
                        }
                    }
                ]
                self.service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
            doc['document_url'] = f"https://docs.google.com/document/d/{doc_id}"
            return GoogleDoc(**doc)

        except HttpError as error:
            logger.error(f"An error occurred while creating the document: {error}")
            return None

    def get_document(self, document_id: str) -> Optional[GoogleDoc]:
        """
        Gets a Google Doc by its ID.
        """
        if not self.service:
            logger.error("GoogleDocsService is not authenticated.")
            return None
        try:
            doc = self.service.documents().get(documentId=document_id).execute()
            doc['document_url'] = f"https://docs.google.com/document/d/{doc['documentId']}"
            return GoogleDoc(**doc)
        except HttpError as error:
            logger.error(f"An error occurred while getting the document: {error}")
            return None

    def update_document_body(self, document_id: str, body_content: str) -> Optional[GoogleDoc]:
        """
        Replaces the entire body of a Google Doc with new content.
        """
        if not self.service:
            logger.error("GoogleDocsService is not authenticated.")
            return None
        try:
            # To replace content, we first need to get the current document size
            # to delete it, then insert the new content.
            document = self.service.documents().get(documentId=document_id, fields='body(content)').execute()
            content = document.get('body', {}).get('content', [])
            
            requests = []
            if content:
                # The last element in the content list has the final end index.
                last_element = content[-1]
                end_index = last_element.get('endIndex')
                
                # We can only delete if there's a valid range. The body always starts at 1.
                if end_index and end_index > 1:
                    requests.append({
                        'deleteContentRange': {
                            'range': { 'startIndex': 1, 'endIndex': end_index - 1 }
                        }
                    })

            if body_content:
                requests.append({
                    'insertText': { 'location': { 'index': 1 }, 'text': body_content }
                })

            if requests:
                self.service.documents().batchUpdate(
                    documentId=document_id, body={'requests': requests}
                ).execute()
            
            # Return the updated document object
            return self.get_document(document_id)

        except HttpError as error:
            logger.error(f"An error occurred while updating the document: {error}")
            return None