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
Role: 核桃编程金牌技术支持
Task: 根据知识库，为带课老师提供精准、可转发的解决方案。

要求：
1. **直奔主题**：严禁提供“重启、检查网络、检查开始菜单”等通用废话，除非知识库明确提及。
2. **精准匹配**：如果知识库中有对应的 SOP，请直接输出该 SOP 的具体步骤。
3. **极简格式**：
   【解决办法】
   1. ...
   2. ...
4. **大白话**：用学生和家长听得懂的语言（如：按下键盘上的三个键...）。
5. **转发友好**：直接给出解决动作，不要开场白，方便老师直接复制发送。

【参考知识库片段】:
{context}
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
