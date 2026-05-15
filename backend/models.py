from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from backend.database import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    category = Column(String, default="general")
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
