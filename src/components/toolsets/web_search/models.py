from pydantic import BaseModel, Field

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="The query to search for.")
    
class WebSearchResponse(BaseModel):
    results: list[str] = Field(..., description="The results of the web search.")
