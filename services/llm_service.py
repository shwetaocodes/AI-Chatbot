import logging
from fastapi import HTTPException, status
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import settings

logger = logging.getLogger(__name__)

_llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    temperature=settings.OLLAMA_TEMPERATURE,
    num_predict=settings.OLLAMA_MAX_TOKENS,
)

SYSTEM_PROMPT = """You are a helpful AI assistant.
Answer clearly and concisely.
If you don't know something, say so honestly."""


async def get_llm_reply(user_message: str) -> str:
    if not user_message.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty",
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    try:
        logger.info("Sending message to Ollama (model=%s)", settings.OLLAMA_MODEL)
        response = await _llm.ainvoke(messages)
        reply = response.content
        logger.info("Ollama replied successfully (chars=%d)", len(reply))
        return reply

    except Exception as e:
        if "connect" in str(e).lower():
            logger.error("Cannot connect to Ollama at %s", settings.OLLAMA_BASE_URL)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM service unavailable — make sure Ollama is running.",
            )
        logger.error("Ollama error: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM service unavailable.",
        )