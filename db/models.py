import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    company = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(200))
    company_size = Column(Integer)
    linkedin_url = Column(String(500))
    score = Column(Float, default=0.0)
    icp_match = Column(Float, default=0.0)
    source = Column(String(50))
    status = Column(String(50), default="new")
    enrichment = Column(JSON, default=lambda: {})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Sequence(Base):
    __tablename__ = "sequences"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    step = Column(Integer, default=1)
    template_name = Column(String(100))
    sent_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    replied_at = Column(DateTime)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    direction = Column(String(20))
    content = Column(Text)
    sentiment = Column(String(50))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
