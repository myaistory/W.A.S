import json
import numpy as np
import os
import sqlite3
import argparse
import sys

# 设置路径，确保在任何地方运行都能找到项目根目录
BASE_DIR = "/home/lianwei_zlw/Walnut-AI-Support"
sys.path.append(BASE_DIR)
from core.logger import logger

class VectorSearchEngine:
    def __init__(self, kb_path: str = f"{BASE_DIR}/data/walnut_kb.json", db_path: str = f"{BASE_DIR}/data/vector_store.db"):
        self.kb_path = kb_path
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS knowledge 
                         (id INTEGER PRIMARY KEY, title TEXT, content TEXT, vector BLOB)''')
        conn.commit()
        conn.close()

    def _get_vector(self, text: str):
        # 暂时使用随机种子向量，后期可接入实际 Embedding
        np.random.seed(hash(text) % (2**32))
        return np.random.rand(128).astype(np.float32)

    def rebuild(self):
        logger.info(f"[Vector] Rebuilding index from {self.kb_path}...")
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM knowledge")
        for item in kb_data:
            text = f"{item.get('title', '')} {item.get('content', '')}"
            vec = self._get_vector(text).tobytes()
            cursor.execute("INSERT INTO knowledge (title, content, vector) VALUES (?, ?, ?)",
                           (item.get('title'), item.get('content'), vec))
        conn.commit()
        conn.close()
        logger.info(f"[Vector] Rebuild complete. {len(kb_data)} items indexed.")

    def search(self, query: str, top_k: int = 2, threshold: float = 0.3) -> str:
        query_vec = self._get_vector(query)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title, content, vector FROM knowledge")
        
        results = []
        for title, content, vec_blob in cursor.fetchall():
            item_vec = np.frombuffer(vec_blob, dtype=np.float32)
            similarity = np.dot(query_vec, item_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(item_vec))
            if similarity >= threshold:
                results.append((similarity, f"问题: {title}\n解决方案: {content}"))
        
        conn.close()
        results.sort(key=lambda x: x[0], reverse=True)
        
        if not results:
            return "NO_MATCH"
        
        return "\n---\n".join([r[1] for r in results[:top_k]])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    engine = VectorSearchEngine()
    if args.rebuild:
        engine.rebuild()
