import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 生成随机密钥，用于会话
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))  # 默认1小时

# 存储活跃会话（实际生产环境应使用Redis等）
active_sessions: Dict[str, Dict] = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def create_session_token() -> str:
    """创建会话令牌"""
    return secrets.token_urlsafe(32)

def create_session(user_id: int, username: str) -> Dict:
    """创建新的用户会话"""
    token = create_session_token()
    expires = datetime.now() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    session_data = {
        "token": token,
        "user_id": user_id,
        "username": username,
        "expires": expires
    }
    
    active_sessions[token] = session_data
    return session_data

def validate_session(token: str) -> Optional[Dict]:
    """验证会话有效性"""
    session = active_sessions.get(token)
    
    if not session:
        return None
        
    if datetime.now() > session["expires"]:
        # 会话已过期，删除
        del active_sessions[token]
        return None
        
    return session

def invalidate_session(token: str) -> bool:
    """使会话无效（退出登录）"""
    if token in active_sessions:
        del active_sessions[token]
        return True
    return False 