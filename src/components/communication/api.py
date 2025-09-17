from fastapi import APIRouter, Depends, HTTPException
from .manager import CommunicationManager
from .models import ChatRequest, ChatResponse
from src.core.dependencies import get_communication_manager
import logging
from fastapi import APIRouter, Depends, HTTPException
from .manager import CommunicationManager
from .models import ChatRequest, ChatResponse
from src.core.dependencies import get_communication_manager
from src.core.security import get_current_active_user
from src.core.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    comm_manager: CommunicationManager = Depends(get_communication_manager),
    current_user: User = Depends(get_current_active_user)
):
    try:
        response_data = await comm_manager.handle_user_request(
            user_input=request.user_input,
            casefile_id=request.casefile_id,
            current_user=current_user
        )
        return ChatResponse(**response_data)
    except Exception as e:
        logger.exception(f"Error handling chat request: {e}") # Log the full traceback
        raise HTTPException(status_code=500, detail="Internal Server Error") # Return a generic error to the client
