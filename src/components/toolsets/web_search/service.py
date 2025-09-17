import logging
from src.components.toolsets.web_search.models import WebSearchRequest, WebSearchResponse
from default_api import google_web_search

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self):
        pass

    def search(self, request: WebSearchRequest) -> WebSearchResponse:
        logger.info(f"Searching web for query: {request.query}")
        search_results = google_web_search(query=request.query)
        return WebSearchResponse(results=[str(search_results)])

def get_web_search_service() -> WebSearchService:
    return WebSearchService()
