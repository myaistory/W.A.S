import requests
import json
import os
from dotenv import load_dotenv

# 强制重新加载，确保读取最新注入的 Key
load_dotenv(override=True)

class GroqEngine:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.url = 'https://api.groq.com/openai/v1/chat/completions'
        try:
            with open('/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json', 'r', encoding='utf-8') as f:
                self.kb_content = f.read()
        except:
            self.kb_content = 'Knowledge base empty.'

    def ask(self, user_query):
        if not self.api_key or len(self.api_key) < 10:
            return '[W.A.S. ERROR] Groq Key Missing or Invalid.'

        prompt = f"""
Role: 核桃编程金牌技术支持工程师
Task: 根据提供的【内部知识库】专业回复老师。

【内部知识库内容】:
{self.kb_content}

【老师的问题】:
{user_query}

要求：专业、礼貌、直接。
"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1
        }
        try:
            r = requests.post(self.url, headers=headers, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
            else:
                # 打印详细错误方便 Boss 诊断
                return f'[SYSTEM_ERROR] Groq API {r.status_code}: {r.text}'
        except Exception as e:
            return f'[SYSTEM_ERROR] Connection Failed: {str(e)}'

ai_engine = GroqEngine()
