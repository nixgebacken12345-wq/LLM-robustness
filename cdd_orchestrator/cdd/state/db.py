from datetime import datetime
from sqlalchemy import create_all, Column, Integer, String, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from cdd.config import settings

Base = declarative_base()

class FileRegistry(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    path = Column(String(512), unique=True, nullable=False)
    last_commit_hash = Column(String(64))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    functions = relationship("FunctionRegistry", back_populates="file", cascade="all, delete-orphan")

class FunctionRegistry(Base):
    __tablename__ = "functions"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    name = Column(String(255), nullable=False)
    signature = Column(Text, nullable=False)
    docstring = Column(Text)
    body_hash = Column(String(64))
    
    file = relationship("FileRegistry", back_populates="functions")

# Resource Lifecycle Management: Database Engine
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes tables. Deterministic and safe to call on startup."""
    Base.metadata.create_all(bind=engine)