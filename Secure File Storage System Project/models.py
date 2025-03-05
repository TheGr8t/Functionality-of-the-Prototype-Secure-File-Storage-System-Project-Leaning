from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

# ✅ User Model (Stores User Accounts)
class Users(Base):
    __tablename__ = "users"  # ✅ Use "users", NOT "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # Role: "user" or "admin"

# ✅ File Model (Stores Uploaded Files)
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Link to User
    filename = Column(String(255), nullable=False)
    encrypted_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(20), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

# ✅ Access Logs (Tracks Users Actions)
class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

# ✅ File Permissions (For Sharing)
class FilePermission(Base):
    __tablename__ = "file_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(String(20), nullable=False)
