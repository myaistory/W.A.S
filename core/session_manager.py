import sqlite3
import json
import os
from core.logger import logger

class PersistentSessionManager:
    def __init__(self, db_path: str = "data/sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions 
                         (user_id TEXT PRIMARY KEY, history TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def get_context(self, user_id: str) -> list:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT history FROM sessions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else []

    def add_message(self, user_id: str, role: str, content: str, max_history: int = 10):
        history = self.get_context(user_id)
        history.append({"role": role, "content": content})
        history = history[-max_history:]  # 保持窗口
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO sessions (user_id, history, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                       (user_id, json.dumps(history)))
        conn.commit()
        conn.close()

# 单例
session_manager = PersistentSessionManager()
