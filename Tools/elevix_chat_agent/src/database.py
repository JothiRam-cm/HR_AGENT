import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String, default="user") # 'user', 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String, unique=True)
    size_bytes = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    session_id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)

    session = relationship("ChatSession", back_populates="messages")

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///./chat_history.db"):
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    # --- User Management ---
    def create_user(self, email, password_hash, full_name, role="user"):
        with self.get_session() as session:
            user = User(email=email, password_hash=password_hash, full_name=full_name, role=role)
            session.add(user)
            session.commit()
            session.refresh(user)  # Ensure ID is populated
            # Extract data before session closes
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            }

    def get_user_by_email(self, email):
        with self.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "full_name": user.full_name,
                    "role": user.role
                }
            return None

    def get_user_by_id(self, user_id):
        with self.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
            return None

    # --- File Management ---
    def add_file_record(self, filename, size_bytes):
        with self.get_session() as session:
            if not session.query(UploadedFile).filter_by(filename=filename).first():
                file_rec = UploadedFile(filename=filename, size_bytes=size_bytes)
                session.add(file_rec)
                session.commit()
                return True
        return False

    def get_all_files(self):
        with self.get_session() as session:
            files = session.query(UploadedFile).all()
            return [{"filename": f.filename, "size_bytes": f.size_bytes, "uploaded_at": f.uploaded_at.isoformat()} for f in files]

    def delete_file_record(self, filename):
        with self.get_session() as session:
            session.query(UploadedFile).filter(UploadedFile.filename == filename).delete()
            session.commit()

    # --- Session & Chat ---
    def create_session_if_not_exists(self, session_id: str, user_id: Optional[int] = None):
        with self.get_session() as session:
            db_session = session.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not db_session:
                db_session = ChatSession(session_id=session_id, user_id=user_id)
                session.add(db_session)
                session.commit()
            elif user_id and not db_session.user_id:
                # Link existing session to user if not linked
                db_session.user_id = user_id
                session.commit()

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None):
        self.create_session_if_not_exists(session_id, user_id)
        with self.get_session() as session:
            message = Message(
                session_id=session_id,
                role=role,
                content=content,
                metadata_json=json.dumps(metadata) if metadata else None
            )
            session.add(message)
            session.commit()

    def get_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_session() as session:
            messages = session.query(Message)\
                .filter(Message.session_id == session_id)\
                .order_by(Message.timestamp.desc())\
                .limit(limit)\
                .all()
            
            result = []
            for msg in reversed(messages):
                result.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": json.loads(msg.metadata_json) if msg.metadata_json else None
                })
            return result
    
    def get_user_sessions(self, user_id: int):
        with self.get_session() as session:
            sessions = session.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()
            results = []
            for s in sessions:
                # Get last message for preview
                last_msg = session.query(Message).filter(Message.session_id == s.session_id).order_by(Message.timestamp.desc()).first()
                preview = last_msg.content[:50] + "..." if last_msg else "New Chat"
                results.append({
                    "session_id": s.session_id,
                    "created_at": s.created_at.isoformat(),
                    "preview": preview
                })
            return results

    def nuke_db(self):
        """Clears all data"""
        Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
