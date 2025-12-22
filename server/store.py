from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, AgentModel, TaskModel, UserModel
from datetime import datetime
import uuid

DB_URL = "sqlite:///./c2_framework.db"

class DataStore:
    def __init__(self):
        self.engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def register_agent(self, agent_id: str, info: dict = None, version: str = "1.0.0"):
        with self.SessionLocal() as db:
            agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
            if not agent:
                agent = AgentModel(id=agent_id, last_seen=datetime.utcnow(), info=info, version=version)
                db.add(agent)
                db.commit()
            else:
                agent.last_seen = datetime.utcnow()
                if info: agent.info = info
                if version: agent.version = version
                agent.status = "online"
                db.commit()

    def add_task(self, agent_id: str, task_type: str, payload: dict, expires_at: datetime):
        with self.SessionLocal() as db:
            task_id = str(uuid.uuid4())
            new_task = TaskModel(
                id=task_id,
                agent_id=agent_id,
                type=task_type,
                payload=payload,
                expires_at=expires_at,
                status="pending"
            )
            db.add(new_task)
            db.commit()
            return task_id

    def get_pending_tasks(self, agent_id: str):
        with self.SessionLocal() as db:
            tasks = db.query(TaskModel).filter(
                TaskModel.agent_id == agent_id,
                TaskModel.status == "pending",
                TaskModel.expires_at > datetime.utcnow()
            ).all()
            
            # Transition to 'leased'
            if tasks:
                for t in tasks:
                    t.status = "leased"
                    t.leased_at = datetime.utcnow()
                db.commit()
            return tasks

    def update_task_result(self, task_id: str, result: dict):
        with self.SessionLocal() as db:
            task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if task:
                task.result = result
                task.status = "completed" if result.get("status") != "error" else "failed"
                task.completed_at = datetime.utcnow()
                db.commit()

    def get_all_agents(self):
        # Auto-set offline status if not seen for 1 minute
        with self.SessionLocal() as db:
            agents = db.query(AgentModel).all()
            for agent in agents:
                if (datetime.utcnow() - agent.last_seen).total_seconds() > 60:
                    agent.status = "offline"
            db.commit()
            return agents

    def get_all_tasks(self, limit=50):
        with self.SessionLocal() as db:
            return db.query(TaskModel).order_by(TaskModel.created_at.desc()).limit(limit).all()

    def get_agent_tasks(self, agent_id: str):
        with self.SessionLocal() as db:
            return db.query(TaskModel).filter(TaskModel.agent_id == agent_id).order_by(TaskModel.created_at.desc()).all()

    def get_stats(self):
        with self.SessionLocal() as db:
            from sqlalchemy import func
            agent_count = db.query(AgentModel).count()
            online_count = db.query(AgentModel).filter(AgentModel.status == "online").count()
            task_count = db.query(TaskModel).count()
            pending_count = db.query(TaskModel).filter(TaskModel.status == "pending").count()
            return {
                "total_agents": agent_count,
                "online_agents": online_count,
                "total_tasks": task_count,
                "pending_tasks": pending_count
            }

    def get_user(self, username: str):
        with self.SessionLocal() as db:
            return db.query(UserModel).filter(UserModel.username == username).first()

    def create_user(self, username: str, hashed_password: str, role: str = "operator"):
        with self.SessionLocal() as db:
            user = UserModel(username=username, hashed_password=hashed_password, role=role)
            db.add(user)
            db.commit()
            return user
