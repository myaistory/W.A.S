import json
import numpy as np
import os
import sqlite3
from typing import List, Dict
from logger import logger

class VectorSearchEngine:
    def __init__(self, kb_path: str, db_path: str = "data/vector_store.db"):
        self.kb_path = kb_path
        self.db_path = db_path
        self.knowledge_base = []
        self.load_kb()
        self._init_db()

    def load_kb(self):
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
            logger.info(f"[VectorEngine] Loaded {len(self.knowledge_base)} items from KB.")
        except Exception as e:
            logger.error(f"[VectorEngine] KB Load Failed: {e}")
            self.knowledge_base = []

    def _init_db(self):
        """初始化 SQLite 用于存储向量缓存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS embeddings 
                         (id INTEGER PRIMARY KEY, content TEXT, vector BLOB)''')
        conn.commit()
        conn.close()

    def _get_mock_vector(self, text: str):
        """
        临时使用简单的特征向量模拟。
        后期可一键替换为 Groq/OpenAI Embedding API。
        """
        # 简单的哈希向量化，用于演示逻辑闭环
        np.random.seed(hash(text) % (2**32))
        return np.random.rand(128).astype(np.float32)

    def search(self, query: str, top_k: int = 3) -> str:
        """语义检索核心逻辑"""
        if not self.knowledge_base:
            return "Knowledge base is empty."

        query_vec = self._get_mock_vector(query)
        scores = []

        for item in self.knowledge_base:
            item_text = f"{item.get('title', '')} {item.get('content', '')}"
            item_vec = self._get_mock_vector(item_text)
            
            # 计算余弦相似度
            similarity = np.dot(query_vec, item_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(item_vec))
            scores.append((similarity, item_text))

        # 按相似度排序
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # 拼接最相关的上下文
        context = "\n---\n".join([s[1] for s in scores[:top_k]])
        return context

vector_engine = VectorSearchEngine(kb_path="/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json")
