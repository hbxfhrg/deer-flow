"""Authentication models for existing sys_user table."""

from datetime import datetime, UTC
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from deerflow.roleplay import RoleplayBase

class SysUserRow(RoleplayBase):
    __tablename__ = "sys_user"
    
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(32), nullable=False)  # MD5 hash
    nick_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    phonenumber: Mapped[str] = mapped_column(String(11))
    sex: Mapped[str] = mapped_column(String(1))
    avatar: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(1), default="0")  # 0=正常, 1=禁用
    del_flag: Mapped[str] = mapped_column(String(1), default="0")
    login_ip: Mapped[str] = mapped_column(String(128))
    login_date: Mapped[datetime] = mapped_column(DateTime)
    create_by: Mapped[str] = mapped_column(String(64))
    create_time: Mapped[datetime] = mapped_column(DateTime)
    update_by: Mapped[str] = mapped_column(String(64))
    update_time: Mapped[datetime] = mapped_column(DateTime)
    remark: Mapped[str] = mapped_column(String(500))