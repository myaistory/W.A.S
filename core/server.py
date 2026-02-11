from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import json
import requests
import os
import time
from dotenv import load_dotenv

# 引入核心组件
import sys
sys.path.append('/home/lianwei_zlw/Walnut-AI-Support/core')
from rag_engine import ai_engine
from logger import logger
from session_manager import session_manager

load_dotenv()

app = FastAPI(title='Walnut AI Support Node (LLM-Powered)')
START_TIME = time.time()
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')

def get_tenant_access_token():
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    payload = {'app_id': APP_ID, 'app_secret': APP_SECRET}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get('tenant_access_token')
    except Exception as e:
        logger.error(f'[FEISHU] Failed to get token: {e}')
        return None

def send_message(receive_id, content):
    token = get_tenant_access_token()
    if not token: return
    url = f'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'receive_id': receive_id, 'msg_type': 'text', 'content': json.dumps({'text': content})}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        logger.error(f'[FEISHU] Send message failed: {e}')

@app.get("/health")
async def health_check():
    return {"status": "online", "uptime": int(time.time() - START_TIME)}

@app.post('/event')
async def handle_feishu_event(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if 'challenge' in data: return {'challenge': data['challenge']}
    
    event = data.get('event', {})
    message = event.get('message', {})
    sender = event.get('sender', {})
    
    if message and 'content' in message:
        try:
            content_json = json.loads(message['content'])
            text = content_json.get('text', '').strip()
            open_id = sender.get('sender_id', {}).get('open_id')
            
            if text:
                logger.info(f'[INBOUND] User:{open_id} Query:"{text[:50]}"')
                # 异步处理
                background_tasks.add_task(process_and_reply, open_id, text)
        except Exception as e:
            logger.error(f'[PROCESSOR] Error: {e}')
                
    return {'status': 'ok'}

def process_and_reply(open_id, text):
    try:
        # 1. 获取历史记忆
        history = session_manager.get_context(open_id)
        
        # 2. 调用 AI (传入记忆)
        reply = ai_engine.ask(text, history=history)
        
        # 3. 更新记忆 (存入 User 提问 和 Assistant 回复)
        session_manager.add_message(open_id, "user", text)
        session_manager.add_message(open_id, "assistant", reply)
        
        logger.info(f'[OUTBOUND] User:{open_id} Context_Depth:{len(history)}')
        send_message(open_id, reply)
    except Exception as e:
        logger.error(f'[AI_CORE] Async processing failed: {e}')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
