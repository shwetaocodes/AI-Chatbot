from datetime import datetime
from sqlalchemy.orm import mapped_column, MappedColumn, declarative_base
from sqlalchemy import DateTime, func

Base = declarative_base()

class TimestampMixin:
    created_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )