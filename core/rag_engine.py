import requests
import json
import os
from dotenv import load_dotenv
from logger import logger

load_dotenv()

class GroqEngine:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.url = 'https://api.groq.com/openai/v1/chat/completions'
        from vector_engine import VectorSearchEngine
        self.vs_engine = VectorSearchEngine(kb_path='/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json')

    def ask(self, user_query: str, history: list = None):
        """
        user_query: 当前提问
        history: 历史对话列表 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        # P2: 语义检索获取最新上下文
        context = self.vs_engine.search(user_query, top_k=2)
        
        system_prompt = f"""
Role: 核桃编程金牌技术支持工程师 (Walnut Technical Support)
Task: 根据提供的【参考知识库片段】回答老师的问题。

【参考知识库片段】:
{context}

要求：
1. 优先使用知识库中的SOP解决。
2. 语气专业且礼貌。
3. 如果库里没有，礼貌引导联系人工。
4. 直接输出回答内容，不要有'你好'之外的废话。
"""
        # 构建消息流
        messages = [{"role": "system", "content": system_prompt}]
        
        # 注入历史记忆
        if history:
            messages.extend(history)
            
        # 注入当前问题
        messages.append({"role": "user", "content": user_query})

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'llama-3.3-70b-versatile',
            'messages': messages,
            'temperature': 0.1
        }
        try:
            r = requests.post(self.url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
            else:
                logger.error(f"[Groq] API Error: {r.status_code} - {r.text}")
                return f'[SYSTEM_ERROR] Groq API {r.status_code}'
        except Exception as e:
            logger.error(f"[Groq] Connection Failed: {e}")
            return f'[SYSTEM_ERROR] Connection Failed'

ai_engine = GroqEngine()
