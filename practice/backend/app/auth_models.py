"""认证模型 — 对应 sys_user 表"""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SysUserRow(Base):
    __tablename__ = "sys_user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(32), nullable=False)
    nick_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    phonenumber: Mapped[str] = mapped_column(String(11))
    sex: Mapped[str] = mapped_column(String(1))
    avatar: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(1), default="0")
    del_flag: Mapped[str] = mapped_column(String(1), default="0")
    login_ip: Mapped[str] = mapped_column(String(128))
    login_date: Mapped[datetime] = mapped_column(DateTime)
    create_by: Mapped[str] = mapped_column(String(64))
    create_time: Mapped[datetime] = mapped_column(DateTime)
    update_by: Mapped[str] = mapped_column(String(64))
    update_time: Mapped[datetime] = mapped_column(DateTime)
    remark: Mapped[str] = mapped_column(String(500))
