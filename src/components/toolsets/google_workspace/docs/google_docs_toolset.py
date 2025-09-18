import logging
from typing import Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.genai import types as adk_types

from src.components.toolsets.google_workspace.docs.service import GoogleDocsService

logger = logging.getLogger(__name__)


class GoogleDocsToolset(BaseToolset):
    """
    A toolset for interacting with Google Docs.
    """

    def __init__(self, docs_service: Optional[GoogleDocsService] = None):
        super().__init__()
        self.docs_service = docs_service

    def _ensure_service(self):
        """Checks if the Docs service is available."""
        if not self.docs_service:
            raise ConnectionError("GoogleDocsService is not available.")

    def _create_document(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Creates a new Google Document.
        """
        self._ensure_service()
        logger.info(
            f"Toolset is calling docs_service.create_document for title: {title}"
        )
        document = self.docs_service.create_document(title)
        return document.model_dump() if document else None

    def _get_document_content(self, document_id: str) -> Optional[str]:
        """
        Gets the content of a Google Document.
        """
        self._ensure_service()
        logger.info(
            f"Toolset is calling docs_service.get_document_content for ID: {document_id}"
        )
        return self.docs_service.get_document_content(document_id)

    def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        google_doc_schema = adk_types.Schema(
            type=adk_types.SchemaType.OBJECT,
            description="Represents a Google Docs document.",
            properties={
                "document_id": adk_types.Schema(
                    type=adk_types.SchemaType.STRING,
                    description="The unique ID of the document.",
                ),
                "title": adk_types.Schema(
                    type=adk_types.SchemaType.STRING,
                    description="The title of the document.",
                ),
            },
        )

        create_document_declaration = adk_types.FunctionDeclaration(
            name="create_google_doc",
            description="Creates a new, empty Google Docs document with a specified title.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "title": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The title for the new document.",
                    ),
                },
                required=["title"],
            ),
            returns=google_doc_schema,
        )

        get_document_content_declaration = adk_types.FunctionDeclaration(
            name="get_google_doc_content",
            description="Retrieves the text content of a specific Google Docs document by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "document_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the document to retrieve content from.",
                    ),
                },
                required=["document_id"],
            ),
            returns=adk_types.Schema(type=adk_types.SchemaType.STRING),
        )

        return [
            FunctionTool(
                func=self._create_document, declaration=create_document_declaration
            ),
            FunctionTool(
                func=self._get_document_content,
                declaration=get_document_content_declaration,
            ),
        ]