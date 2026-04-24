import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, UUID, text
from core.database import Base
from models.base import TimestampMixin

if TYPE_CHECKING:
    from models.conversation import Conversation

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4  
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True                       
    )
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text('true'), default=True         
    )

    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,                                      
    )