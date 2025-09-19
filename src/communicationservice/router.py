# src/communicationservice/router.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from core.dependencies import get_communication_service
from core.security import User, get_current_active_user

router = APIRouter()

class CommunicationService: # Placeholder
    async def handle_user_request(self, user_input, casefile_id, current_user):
        return {"response": "This is a placeholder response."}


class ChatRequest(BaseModel):
    user_input: str
    casefile_id: str # Made mandatory for clarity

@router.post("/chat", summary="Process a user message.")
async def process_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    comm_service: CommunicationService = Depends(get_communication_service)
):
    """
    This endpoint is the single point of entry for all user chat interactions.
    It requires a valid casefile_id to maintain context.
    """
    try:
        response = await comm_service.handle_user_request(
            user_input=request.user_input,
            casefile_id=request.casefile_id,
            current_user=current_user
        )
        return response
    except ValueError as e:
        # This will catch the error if the casefile_id is not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/test")
async def test_chat_route():
    return {"message": "Chat router test endpoint is working!"}