# src/components/toolsets/google_workspace/docs/service.py

import logging
from typing import Dict, Any
from ..workspace_service import BaseGoogleService
from .models import Document, CreateDocumentQuery, GetDocumentQuery

logger = logging.getLogger(__name__)

class DocsService(BaseGoogleService):
    """Service layer for handling Google Docs business logic."""
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'docs'
        self.service_version = 'v1'
        self.scopes = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/documents.readonly']

    async def create_document(self, user_id: str, query: CreateDocumentQuery) -> Dict[str, Any]:
        """Creates a new Google Document."""
        logger.info(f"Creating a new document titled '{query.title}' for user_id: {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}
        
        try:
            body = {'title': query.title}
            doc = service.documents().create(body=body).execute()
            return Document.model_validate(doc).model_dump()
        except Exception as e:
            logger.error(f"Failed to create document for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def get_document(self, user_id: str, query: GetDocumentQuery) -> Dict[str, Any]:
        """Retrieves a Google Document by its ID."""
        logger.info(f"Retrieving document_id: {query.document_id} for user_id: {user_id}")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}

        try:
            doc = service.documents().get(documentId=query.document_id).execute()
            return Document.model_validate(doc).model_dump()
        except Exception as e:
            logger.error(f"Failed to get document for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}