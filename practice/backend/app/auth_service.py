"""认证服务 — 从 deerflow/roleplay/auth_service.py 迁移"""

import bcrypt
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import select

from app.database import get_db
from app.auth_models import SysUserRow
from app.timezone_utils import now_local


class AuthService:
    @staticmethod
    def _verify_bcrypt_password(password: str, hashed_password: str) -> bool:
        """验证 BCrypt 密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    async def login(username: str, password: str):
        """用户登录认证"""
        async with get_db() as session:
            result = await session.execute(
                select(SysUserRow).where(
                    SysUserRow.user_name == username,
                    SysUserRow.status == "0",
                    SysUserRow.del_flag == "0"
                )
            )
            user = result.scalar_one_or_none()

            if not user:
                return {"success": False, "message": "用户名不存在或已禁用"}

            if not AuthService._verify_bcrypt_password(password, user.password):
                return {"success": False, "message": "密码错误"}

            token = str(uuid4())
            token_expire = now_local() + timedelta(hours=24)

            user.login_ip = "127.0.0.1"
            user.login_date = now_local()
            await session.commit()

            return {
                "success": True,
                "message": "登录成功",
                "data": {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "nick_name": user.nick_name,
                    "email": user.email,
                    "phonenumber": user.phonenumber,
                    "token": token,
                    "expire_time": token_expire.isoformat()
                }
            }

    @staticmethod
    async def get_user_info(user_id: int):
        """获取用户信息"""
        async with get_db() as session:
            result = await session.execute(
                select(SysUserRow).where(
                    SysUserRow.user_id == user_id,
                    SysUserRow.status == "0",
                    SysUserRow.del_flag == "0"
                )
            )
            user = result.scalar_one_or_none()

            if not user:
                return {"success": False, "message": "用户不存在"}

            return {
                "success": True,
                "data": {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "nick_name": user.nick_name,
                    "email": user.email,
                    "phonenumber": user.phonenumber,
                    "sex": user.sex,
                    "create_time": user.create_time.isoformat() if user.create_time else None,
                    "remark": user.remark
                }
            }
