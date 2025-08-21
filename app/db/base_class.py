# app/db/base_class.py
# This file defines the base class that all our SQLAlchemy ORM models will inherit from.
import uuid
from typing import Any
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

# Create a declarative base class
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True  # This class won't form its own table

    # Generate a UUID primary key by default
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
    )
    
    # Automatic timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Generate __tablename__ automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase class name to snake_case for the table name
        # e.g., 'UserProfile' becomes 'user_profile'
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        return name + 's'  # Simple pluralization (adds 's')