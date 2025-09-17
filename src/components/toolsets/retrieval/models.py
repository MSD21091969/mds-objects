from pydantic import BaseModel, Field

class RetrievalRequest(BaseModel):
    query: str = Field(..., description="The query to search for.")
    
class RetrievalResponse(BaseModel):
    results: list[str] = Field(..., description="The results of the retrieval.")
