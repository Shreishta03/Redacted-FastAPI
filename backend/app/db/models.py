from sqlalchemy import Column, Integer, Text, DateTime, String, Boolean
from sqlalchemy.sql import func
from .database import Base

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class RedactionLog(Base):
    __tablename__ = "redaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    input_type = Column(Text, nullable=False)
    source_name = Column(Text, nullable=False)
    entity_count = Column(Integer)
    columns_redacted = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)
    upload_limit = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())