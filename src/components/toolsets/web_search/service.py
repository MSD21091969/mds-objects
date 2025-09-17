import logging
from src.components.toolsets.web_search.models import WebSearchRequest, WebSearchResponse

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self, web_search_function=None):
        self.web_search_function = web_search_function

    def search(self, request: WebSearchRequest) -> WebSearchResponse:
        logger.info(f"Searching web for query: {request.query}")
        if self.web_search_function:
            search_results = self.web_search_function(query=request.query)
        else:
            search_results = {"error": "Web search function not provided."}
        return WebSearchResponse(results=[str(search_results)])

def get_web_search_service() -> WebSearchService:
    return WebSearchService()
