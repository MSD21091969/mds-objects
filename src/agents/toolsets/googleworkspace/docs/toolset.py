# src/components/toolsets/google_workspace/docs/google_docs_toolset.py

import logging
from typing import Optional

from google.adk.tools import FunctionTool, BaseToolset, ToolContext, ReadonlyContext, Parameter
from google.adk.tools.base_tool import BaseTool

from .service import DocsService
from .models import CreateDocumentQuery, GetDocumentQuery

logger = logging.getLogger(__name__)

class DocsToolset(BaseToolset):
    """Exposes DocsService methods as ADK Tools."""
    def __init__(self, docs_service: DocsService):
        self.docs_service = docs_service

    async def get_tools(self, readonly_context: Optional[ReadonlyContext] = None) -> list[BaseTool]:
        
        async def _create_document_tool(title: str, tool_context: ToolContext) -> dict:
            """Creates a new Google Document with a specified title."""
            user_id = tool_context.invocation_context.session.user_id
            validated_input = CreateDocumentQuery(title=title)
            return await self.docs_service.create_document(user_id=user_id, query=validated_input)

        async def _get_document_tool(document_id: str, tool_context: ToolContext) -> dict:
            """Retrieves the content and metadata of a specific Google Document by its ID."""
            user_id = tool_context.invocation_context.session.user_id
            validated_input = GetDocumentQuery(document_id=document_id)
            return await self.docs_service.get_document(user_id=user_id, query=validated_input)

        tools = [
            FunctionTool(
                func=_create_document_tool,
                name="docs_create_document",
                description="Creates a new Google Document in the user's account.",
                parameters=[
                    Parameter(
                        name="title",
                        type=str,
                        description="The title for the new document. It must be provided by the user.",
                        required=True
                    )
                ]
            ),
            FunctionTool(
                func=_get_document_tool,
                name="docs_get_document",
                description="Retrieves the content and metadata of a specific Google Document by its unique ID. This tool is useful for getting the full content of a document to summarize or analyze it.",
                parameters=[
                    Parameter(
                        name="document_id",
                        type=str,
                        description="The unique ID of the Google Document. This ID can be found in the document's URL.",
                        required=True
                    )
                ]
            )
        ]
        return tools