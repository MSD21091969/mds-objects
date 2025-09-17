import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types
from typing import List

from src.components.toolsets.google_workspace.docs.service import GoogleDocsService
from src.components.toolsets.google_workspace.docs.models import Document

logger = logging.getLogger(__name__)

class DocsToolset(BaseToolset):
    """A toolset for interacting with Google Docs."""

    def __init__(self, client_secrets_path: str, token_path: str = "token.json"):
        self.docs_service = GoogleDocsService(client_secrets_path, token_path)
        super().__init__()

    def _get_document_content(self, document_id: str) -> str:
        """Gets the content of a specific Google Doc by its ID."""
        try:
            content = self.docs_service.get_document_content(document_id)
            return content if content else "Document content not found."
        except Exception as e:
            logger.error(f"Error getting Google Doc content: {e}")
            return f"Error getting Google Doc content: {e}"

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        get_document_content_declaration = adk_types.FunctionDeclaration(
            name="get_google_doc_content",
            description="Gets the content of a specific Google Doc by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "document_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the Google Doc.",
                    ),
                },
                required=["document_id"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="The content of the Google Doc as a string, or 'Document content not found.'.",
            ),
        )

        return [
            FunctionTool(
                func=self._get_document_content,
                declaration=get_document_content_declaration,
            ),
        ]
