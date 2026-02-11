import json
import os
import requests
from dotenv import load_dotenv
from core.logger import logger

load_dotenv()

class IntelligentDistiller:
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.url = 'https://api.groq.com/openai/v1/chat/completions'

    def distill_with_llm(self, raw_content: str):
        """利用 LLM 将原始工单/文档转化为标准 Q&A"""
        prompt = f"""
        你是一个专业的数据清洗专家。请将以下原始技术支持记录提炼为高质量的 RAG 知识点。
        
        【原始记录】:
        {raw_content}
        
        【要求】:
        1. 提取核心问题 (question) 和 最终解决方案 (answer)。
        2. 方案必须是步骤清晰的 SOP (1. 2. 3. ...)。
        3. 剔除所有姓名、手机号、日期等隐私信息。
        4. 生成 2-3 个用户可能会问的同义词 (variants)。
        5. 以 JSON 格式输出: {{"question": "...", "answer": "...", "variants": ["...", "..."]}}
        
        注意：仅输出 JSON，不要有任何开场白。
        """
        
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload = {
            'model': 'llama-3.1-8b-instant', # 使用小模型进行大规模清洗
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.1,
            'response_format': {"type": "json_object"}
        }
        
        try:
            r = requests.post(self.url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"[Distiller] LLM failed: {e}")
        return None

distiller = IntelligentDistiller()
