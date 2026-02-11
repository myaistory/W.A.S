import requests
import json
import os
import base64
from dotenv import load_dotenv
from logger import logger

load_dotenv()

class GroqEngine:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.url = 'https://api.groq.com/openai/v1/chat/completions'
        from vector_engine import VectorSearchEngine
        self.vs_engine = VectorSearchEngine(kb_path='/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json')

    def ask(self, user_query: str, history: list = None, image_base64: str = None):
        """
        支持多模态推理
        image_base64: 图片的 Base64 编码字符串
        """
        # P2: 语义检索获取最新上下文
        context = self.vs_engine.search(user_query, top_k=2)
        
        system_prompt = f"""
Role: 核桃编程金牌技术支持工程师 (Walnut Technical Support)
Task: 根据提供的【参考知识库片段】回答老师的问题。如果老师提供了截图，请分析截图中的报错信息。

【参考知识库片段】:
{context}

要求：
1. 仅根据知识库回答，禁止编造。
2. 如果有图片，请先识别图片中的错误弹窗、文字或异常现象，再匹配 SOP。
3. 语气专业，简洁。
"""
        # 构建消息内容
        content = [{"type": "text", "text": user_query}]
        
        if image_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            })

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": content})

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            # 升级为 Llama 4 Vision 模型
            'model': 'meta-llama/llama-4-maverick-17b-128e-instruct',
            'messages': messages,
            'temperature': 0.1,
            'max_tokens': 1024
        }
        try:
            r = requests.post(self.url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
            else:
                logger.error(f"[Groq-Vision] API Error: {r.status_code} - {r.text}")
                return f'[SYSTEM_ERROR] Vision Core Error {r.status_code}'
        except Exception as e:
            logger.error(f"[Groq-Vision] Connection Failed: {e}")
            return f'[SYSTEM_ERROR] Vision Core Offline'

ai_engine = GroqEngine()
