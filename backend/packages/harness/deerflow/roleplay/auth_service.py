"""Authentication service for existing sys_user table."""

import bcrypt
from datetime import datetime, UTC, timedelta
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from deerflow.roleplay import get_db
from deerflow.roleplay.auth_models import SysUserRow

class AuthService:
    @staticmethod
    def _verify_bcrypt_password(password: str, hashed_password: str) -> bool:
        """Verify password using BCrypt."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    async def login(username: str, password: str):
        """Authenticate user with username and password."""
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
            
            # Verify BCrypt password
            if not AuthService._verify_bcrypt_password(password, user.password):
                return {"success": False, "message": "密码错误"}
            
            # Generate token (simple implementation)
            token = str(uuid4())
            token_expire = datetime.now(UTC) + timedelta(hours=24)
            
            # Update login info
            user.login_ip = "127.0.0.1"  # Should get real IP from request
            user.login_date = datetime.now(UTC)
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
        """Get user information by user ID."""
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
    
    @staticmethod
    async def get_user_by_username(username: str):
        """Get user information by username."""
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
                return None
            
            return {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "nick_name": user.nick_name,
                "email": user.email
            }