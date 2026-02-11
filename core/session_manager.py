from cachetools import TTLCache
from logger import logger

class SessionManager:
    def __init__(self, max_sessions=1000, ttl=1800):
        """
        max_sessions: 最多存储 1000 个活跃用户
        ttl: 会话有效期 30 分钟 (1800秒)
        """
        self.cache = TTLCache(maxsize=max_sessions, ttl=ttl)

    def get_context(self, user_id: str) -> list:
        """获取用户的历史对话"""
        return self.cache.get(user_id, [])

    def add_message(self, user_id: str, role: str, content: str):
        """添加新消息到记忆中，保留最近 10 条"""
        history = self.cache.get(user_id, [])
        history.append({"role": role, "content": content})
        # 截断，保留最近 5 轮对话
        self.cache[user_id] = history[-10:]
        logger.debug(f"[Session] Memory updated for {user_id}. Current depth: {len(self.cache[user_id])}")

    def clear_session(self, user_id: str):
        """清理特定用户的记忆"""
        if user_id in self.cache:
            del self.cache[user_id]

# 全局单例
session_manager = SessionManager()
