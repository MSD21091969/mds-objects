import logging
from typing import Dict, Any, Optional

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types

from src.components.toolsets.google_workspace.docs.service import GoogleDocsService

logger = logging.getLogger(__name__)


class GoogleDocsToolset(BaseToolset):
    """
    A toolset for interacting with Google Docs.
    """

    def __init__(self, docs_service: GoogleDocsService):
        super().__init__()
        self.docs_service = docs_service

    async def _create_document(
        self, title: str, content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Creates a new Google Doc with the given title and content.
        """
        logger.info(f"Creating Google Doc with title: {title}")
        doc = self.docs_service.create_document(title=title, body_content=content)
        return doc.model_dump() if doc else None

    async def _get_document(
        self, document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Gets a Google Doc by its ID.
        """
        logger.info(f"Getting Google Doc with ID: {document_id}")
        doc = self.docs_service.get_document(document_id=document_id)
        return doc.model_dump() if doc else None

    async def _update_document_body(
        self, document_id: str, content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Replaces the entire body of a Google Doc with new content.
        """
        logger.info(f"Updating body of Google Doc with ID: {document_id}")
        doc = self.docs_service.update_document_body(
            document_id=document_id, body_content=content
        )
        return doc.model_dump() if doc else None

    def get_tools(self) -> list[BaseTool]:
        """
        Returns a list of tools provided by this toolset.
        """
        doc_schema = adk_types.Schema(
            type=adk_types.SchemaType.OBJECT,
            properties={
                "document_id": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "title": adk_types.Schema(type=adk_types.SchemaType.STRING),
                "document_url": adk_types.Schema(type=adk_types.SchemaType.STRING),
            },
        )

        create_document_declaration = adk_types.FunctionDeclaration(
            name="create_google_doc",
            description="Creates a new Google Doc with the given title and content.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "title": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The title of the new document.",
                    ),
                    "content": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The content to write to the new document.",
                    ),
                },
                required=["title", "content"],
            ),
            returns=doc_schema,
        )

        get_document_declaration = adk_types.FunctionDeclaration(
            name="get_google_doc",
            description="Gets a Google Doc by its ID.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "document_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the document to retrieve.",
                    )
                },
                required=["document_id"],
            ),
            returns=doc_schema,
        )

        update_document_body_declaration = adk_types.FunctionDeclaration(
            name="update_google_doc_body",
            description="Replaces the entire body of a Google Doc with new content.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "document_id": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The ID of the document to update.",
                    ),
                    "content": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The new content to write to the document.",
                    ),
                },
                required=["document_id", "content"],
            ),
            returns=doc_schema,
        )

        return [
            FunctionTool(
                func=self._create_document, declaration=create_document_declaration
            ),
            FunctionTool(func=self._get_document, declaration=get_document_declaration),
            FunctionTool(
                func=self._update_document_body,
                declaration=update_document_body_declaration,
            ),
        ]
