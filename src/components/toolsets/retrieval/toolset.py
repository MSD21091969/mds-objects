import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.components.toolsets.retrieval.models import RetrievalRequest, RetrievalResponse
from src.components.toolsets.retrieval.service import RetrievalService

logger = logging.getLogger(__name__)

class RetrievalToolset(BaseToolset):
    """A toolset for retrieving information."""

    def __init__(self, retrieval_service: RetrievalService):
        self._retrieval_service = retrieval_service
        super().__init__()

    async def retrieve(self, query: str, tool_context: ToolContext) -> RetrievalResponse:
        """
        Retrieves relevant information for a given query.
        Args:
            query: The search query string.
            tool_context: The runtime context provided by the ADK.
        """
        request = RetrievalRequest(query=query)
        return await self._retrieval_service.retrieve(request)

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        return [
            FunctionTool(func=self.retrieve),
        ]