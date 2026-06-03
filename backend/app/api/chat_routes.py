import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import get_current_active_user
from app.database.session import get_db
from app.models.models import Chat, Message, MessageRole, Repository, ProcessingStatus, User
from app.rag.embeddings import generate_single_embedding
from app.rag.llm import generate_chat_answer
from app.rag.vector_store import collection_exists, retrieve_chunks
from app.schemas.schemas import (
    ChatMessageRequest, ChatMessageResponse, ChatResponse,
    CreateChatRequest, MessageResponse, SourceChunk,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


def _msg_response(msg: Message) -> MessageResponse:
    sources = None
    if msg.sources:
        sources = [SourceChunk(**s) for s in msg.sources]
    return MessageResponse(
        id=msg.id,
        chat_id=msg.chat_id,
        role=msg.role.value,
        content=msg.content,
        sources=sources,
        created_at=msg.created_at,
    )


@router.post("/{repository_id}/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    repository_id: str,
    req: CreateChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id, Repository.user_id == user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")

    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        repository_id=repository_id,
        title=req.title or "New Chat",
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)

    return ChatResponse(
        id=chat.id,
        repository_id=chat.repository_id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=0,
    )


@router.get("/{repository_id}/chats", response_model=list[ChatResponse])
async def list_chats(
    repository_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Chat)
        .where(Chat.repository_id == repository_id, Chat.user_id == user.id)
        .order_by(Chat.updated_at.desc())
    )
    chats = result.scalars().all()

    responses = []
    for chat in chats:
        count_res = await db.execute(
            select(Message).where(Message.chat_id == chat.id)
        )
        msgs = count_res.scalars().all()
        responses.append(ChatResponse(
            id=chat.id,
            repository_id=chat.repository_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(msgs),
        ))
    return responses


@router.get("/{repository_id}/chats/{chat_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    repository_id: str,
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id, Chat.user_id == user.id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat not found")

    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )
    return [_msg_response(m) for m in result.scalars().all()]


@router.post("/{repository_id}/message", response_model=ChatMessageResponse)
async def send_message(
    repository_id: str,
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_active_user),
):
    # Validate repo ownership + status
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id, Repository.user_id == user.id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Repository not found")
    if repo.status != ProcessingStatus.READY:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Repository is not ready (status: {repo.status.value}). Please wait for processing to complete.",
        )

    # Get or create chat
    if req.chat_id:
        result = await db.execute(
            select(Chat).where(Chat.id == req.chat_id, Chat.user_id == user.id)
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Chat not found")
    else:
        title = req.message[:60] + ("..." if len(req.message) > 60 else "")
        chat = Chat(
            id=str(uuid.uuid4()),
            user_id=user.id,
            repository_id=repository_id,
            title=title,
        )
        db.add(chat)
        await db.flush()

    # Save user message
    user_msg = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        role=MessageRole.USER,
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # RAG: embed question + retrieve chunks
    query_emb = generate_single_embedding(req.message)
    chunks = retrieve_chunks(repository_id, query_emb, top_k=7)

    # Generate answer
    answer = generate_chat_answer(req.message, chunks)

    # Build sources list
    sources_data = [
        {
            "file_path": c["file_path"],
            "content": c["content"][:600],
            "score": c["score"],
            "chunk_type": c.get("chunk_type"),
            "function_name": c.get("function_name"),
            "language": c.get("language"),
            "start_line": c.get("start_line"),
            "end_line": c.get("end_line"),
        }
        for c in chunks
    ]

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        role=MessageRole.ASSISTANT,
        content=answer,
        sources=sources_data,
    )
    db.add(assistant_msg)

    # Update chat title if first message
    from sqlalchemy import func
    count_res = await db.execute(
        select(func.count(Message.id)).where(Message.chat_id == chat.id)
    )
    if (count_res.scalar() or 0) <= 2:
        chat.title = req.message[:60] + ("..." if len(req.message) > 60 else "")

    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(assistant_msg)

    return ChatMessageResponse(
        chat_id=chat.id,
        user_message=_msg_response(user_msg),
        assistant_message=_msg_response(assistant_msg),
    )
