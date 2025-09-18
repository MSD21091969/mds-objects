import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext

from src.components.toolsets.web_search.models import WebSearchRequest, WebSearchResponse
from src.components.toolsets.web_search.service import WebSearchService

logger = logging.getLogger(__name__)

class WebSearchToolset(BaseToolset):
    """A toolset for searching the web."""

    def __init__(self, web_search_service: WebSearchService):
        self._web_search_service = web_search_service
        super().__init__()

    async def search(self, query: str, tool_context: ToolContext) -> WebSearchResponse:
        """
        Searches the web for a given query.
        Args:
            query: The search query string.
            tool_context: The runtime context provided by the ADK.
        """
        request = WebSearchRequest(query=query)
        return await self._web_search_service.search(request)

    async def get_tools(self, tool_context: "ToolContext") -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        return [
            FunctionTool(func=self.search),
        ]