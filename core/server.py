from fastapi import FastAPI, Request
import uvicorn
import json
import requests
import os
import time
from dotenv import load_dotenv

# 引入 Groq 引擎
import sys
sys.path.append('/home/lianwei_zlw/Walnut-AI-Support/core')
from rag_engine import GroqEngine

load_dotenv()

app = FastAPI(title='Walnut AI Support Node (LLM-Powered)')
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')

# 实例化 Groq 引擎
try:
    ai_engine = GroqEngine()
    print('[W.A.S.] GroqEngine Loaded Successfully.')
except Exception as e:
    print(f'[W.A.S.] GroqEngine Init Failed: {e}')
    ai_engine = None

def get_tenant_access_token():
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    payload = {'app_id': APP_ID, 'app_secret': APP_SECRET}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get('tenant_access_token')
    except Exception as e:
        print(f'[ERROR] Failed to get token: {e}')
        return None

def send_message(receive_id, content):
    token = get_tenant_access_token()
    if not token: 
        print('[ERROR] No tenant_token available')
        return
        
    url = f'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {
        'receive_id': receive_id,
        'msg_type': 'text',
        'content': json.dumps({'text': content})
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f'[W.A.S.] API RESP: {r.status_code} - {r.text}')
    except Exception as e:
        print(f'[ERROR] Send message failed: {e}')

@app.post('/event')
async def handle_feishu_event(request: Request):
    data = await request.json()
    
    # URL 验证
    if 'challenge' in data:
        return {'challenge': data['challenge']}
    
    # 消息处理
    event = data.get('event', {})
    message = event.get('message', {})
    sender = event.get('sender', {})
    
    if message and 'content' in message:
        try:
            content_json = json.loads(message['content'])
            text = content_json.get('text', '').strip()
            open_id = sender.get('sender_id', {}).get('open_id')
            
            if text:
                print(f'[W.A.S.] INBOUND -> {open_id}: {text}')
                
                # 如果 AI 引擎不可用，使用简单兜底
                if not ai_engine:
                    reply = '【系统提示】AI 核心初始化失败，请联系管理员检查 API Key。'
                else:
                    reply = ai_engine.ask(text)
                
                send_message(open_id, reply)
        except Exception as e:
            print(f'[ERROR] Internal processing error: {e}')
                
    return {'status': 'ok'}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
