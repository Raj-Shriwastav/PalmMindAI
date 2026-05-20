from fastapi import APIRouter, HTTPException, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.agent import AgentService

router = APIRouter(tags=["Agent Chat"])

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_turn(request: ChatRequest):
    """Submits a conversation prompt to the stateful LangGraph agent machine, returning responses and history turns."""
    try:
        # Trigger asynchronous Agent Service execution
        response = await AgentService.chat(
            session_id=request.session_id,
            message=request.message
        )
        return response
    except Exception as e:
        # Handle exceptions gracefully returning 500 error code
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred within the Agentic processing loop: {str(e)}"
        )
