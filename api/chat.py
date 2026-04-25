import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from schemas.chat import ChatRequest, ChatResponse
from services.llm_service import get_llm_reply

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message and get an LLM reply",
)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stateless chat endpoint — no memory yet.
    Each request is independent.

    - Requires valid JWT in Authorization header
    - Returns LLM reply with a new message_id
    - conversation_id echoed back (or new UUID if null)
    """
    conversation_id = body.conversation_id or uuid.uuid4()

    reply = await get_llm_reply(body.message)

    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        message_id=uuid.uuid4(),
    )
