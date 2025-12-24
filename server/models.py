from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True)
    status = Column(String, default="online") # online, offline, busy
    version = Column(String, default="1.0.0")
    last_seen = Column(DateTime, default=datetime.utcnow)
    info = Column(JSON, nullable=True) # Metadata: OS, User, etc.
    agent_type = Column(String, default="binary") # binary, web
    tasks = relationship("TaskModel", back_populates="agent", cascade="all, delete-orphan")

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"))
    type = Column(String) # shell, sysinfo, etc.
    payload = Column(JSON)
    status = Column(String, default="pending") # pending, leased, completed, failed, expired
    result = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    leased_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime)
    
    agent = relationship("AgentModel", back_populates="tasks")

class UserModel(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    hashed_password = Column(String)
    role = Column(String, default="operator")
