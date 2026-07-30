import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.database.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True) # Nullable for Google OAuth logins
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default="uploaded") # uploaded, processing, analyzed, failed
    file_type = Column(String(50), nullable=False) # PDF, Excel, CSV, Image
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
