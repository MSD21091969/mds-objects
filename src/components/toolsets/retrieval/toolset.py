import logging
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.base_tool import BaseTool
from google.genai import types as adk_types

from src.components.toolsets.retrieval.models import RetrievalRequest
from src.components.toolsets.retrieval.service import RetrievalService

logger = logging.getLogger(__name__)

class RetrievalToolset(BaseToolset):
    """A toolset for retrieving information."""

    def __init__(self, retrieval_service: RetrievalService):
        self.retrieval_service = retrieval_service
        super().__init__()

    def _retrieve(self, query: str) -> str:
        """Retrieves relevant information for a given query."""
        request = RetrievalRequest(query=query)
        response = self.retrieval_service.retrieve(request)
        return "\n".join(response.results)

    def get_tools(self) -> list[BaseTool]:
        """Returns a list of all the tool methods in this toolset."""
        retrieve_declaration = adk_types.FunctionDeclaration(
            name="retrieve",
            description="Retrieves relevant information for a given query.",
            parameters=adk_types.Schema(
                type=adk_types.SchemaType.OBJECT,
                properties={
                    "query": adk_types.Schema(
                        type=adk_types.SchemaType.STRING,
                        description="The query to retrieve information for.",
                    ),
                },
                required=["query"],
            ),
            returns=adk_types.Schema(
                type=adk_types.SchemaType.STRING,
                description="A string containing the retrieved information.",
            ),
        )

        return [
            FunctionTool(
                func=self._retrieve,
                declaration=retrieve_declaration,
            ),
        ]