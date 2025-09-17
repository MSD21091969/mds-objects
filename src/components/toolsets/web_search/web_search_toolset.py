import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types

from src.components.toolsets.web_search.models import WebSearchRequest
from src.components.toolsets.web_search.service import WebSearchService

logger = logging.getLogger(__name__)

class WebSearchToolset(BaseToolset):
    """A toolset for searching the web."""

    def __init__(self, web_search_service: WebSearchService):
        self.web_search_service = web_search_service
        super().__init__()

    def _search(self, query: str) -> str:
        """Searches the web for a given query."""
        request = WebSearchRequest(query=query)
        response = self.web_search_service.search(request)
        return "\n".join(response.results)

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        search_declaration = adk_types.FunctionDeclaration(
            name="search",
            description="Searches the web for a given query.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "query": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The query to search the web for.",
                    ),
                },
                required=["query"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A string containing the search results.",
            ),
        )

        return [
            FunctionTool(
                func=self._search,
                declaration=search_declaration,
            ),
        ]