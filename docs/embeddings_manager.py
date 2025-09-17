# MDSAPP/core/managers/embeddings_manager.py

import logging
from typing import List, TYPE_CHECKING
import os

# Updated imports
from MDSAPP.CasefileManagement.models.casefile import Casefile
from MDSAPP.core.managers.database_manager import DatabaseManager
from MDSAPP.core.utils.document_parser import DocumentParser
# Removed direct import: from MDSAPP.core.services.google_workspace_manager import GoogleWorkspaceManager

# Type hinting for GoogleWorkspaceManager
if TYPE_CHECKING:
    from MDSAPP.core.services.google_workspace_manager import GoogleWorkspaceManager

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """
    Manages the generation and storage of vector embeddings for documents.
    """
    def __init__(
        self,
        db_manager: DatabaseManager,
        parser: DocumentParser,
        google_workspace_manager: "GoogleWorkspaceManager" = None # Made optional
    ):
        self.db_manager = db_manager
        self.parser = parser
        self.google_workspace_manager = google_workspace_manager # Store the new dependency
        self.embedding_model = self.db_manager.embedding_model
        logger.info("EmbeddingsManager initialized.")

    def set_google_workspace_manager(self, google_workspace_manager: "GoogleWorkspaceManager"):
        """
        Injects the GoogleWorkspaceManager after initialization to resolve circular dependency.
        """
        self.google_workspace_manager = google_workspace_manager
        logger.info("GoogleWorkspaceManager injected into EmbeddingsManager.")
        
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]
