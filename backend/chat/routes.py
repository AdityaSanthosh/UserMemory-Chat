from auth.dependencies import get_current_user
from database.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from .models import ChatRequest, ConversationDetail, ConversationListItem
from .service import chat_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/conversations", response_model=list[ConversationListItem])
async def list_conversations(current_user: User = Depends(get_current_user)):
    """List all chat conversations for the current user"""
    conversations = await chat_service.get_user_conversations(current_user.id)
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str, current_user: User = Depends(get_current_user)
):
    """Get a specific conversation with its message history"""
    conversation = await chat_service.get_conversation_messages(
        current_user.id, conversation_id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="conversation not found"
        )

    return conversation


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: str, current_user: User = Depends(get_current_user)
):
    """Delete a specific conversation"""
    success = await chat_service.delete_conversation(current_user.id, conversation_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )

    return None


@router.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Send a message and receive streaming response via SSE"""
    return StreamingResponse(
        chat_service.stream_chat(
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            message=request.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
