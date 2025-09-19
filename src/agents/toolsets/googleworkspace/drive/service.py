# src/components/toolsets/google_workspace/drive/service.py

import logging
from typing import Dict, Any, Optional
from ..workspace_service import BaseGoogleService
from .models import FileList

logger = logging.getLogger(__name__)

class DriveService(BaseGoogleService):
    """Service layer for handling Google Drive business logic."""
    def __init__(self, credential_manager):
        super().__init__(credential_manager)
        self.service_name = 'drive'
        self.service_version = 'v3'
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']

    async def list_files(self, user_id: str, query: str, page_size: int = 20) -> Dict[str, Any]:
        """Lists files in the user's Google Drive."""
        logger.info(f"Listing Drive files for user_id: {user_id} with query: '{query}'")
        service = await self.get_service(user_id)
        if not service:
            return {"status": "error", "message": "Failed to authenticate with Google."}
        
        try:
            results = service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, parents)"
            ).execute()
            return FileList.model_validate(results).model_dump()
        except Exception as e:
            logger.error(f"Failed to list Drive files for user {user_id}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}