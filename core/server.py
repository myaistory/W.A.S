from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import json
import requests
import os
import time
import base64
from dotenv import load_dotenv

# 引入核心组件
import sys
sys.path.append('/home/lianwei_zlw/Walnut-AI-Support/core')
from rag_engine import ai_engine
from logger import logger
from session_manager import session_manager

load_dotenv()

app = FastAPI(title='Walnut AI Support Node (Vision-Enabled)')
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
        logger.error(f'[FEISHU] Token Error: {e}')
        return None

def get_image_base64(message_id, image_key):
    """从飞书下载图片并转为 Base64"""
    token = get_tenant_access_token()
    if not token: return None
    
    url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/resources/{image_key}?type=image"
    headers = {'Authorization': f'Bearer {token}'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
        logger.error(f"[FEISHU] Image Download Failed: {r.status_code}")
    except Exception as e:
        logger.error(f"[FEISHU] Image API Error: {e}")
    return None

def send_message(receive_id, content):
    token = get_tenant_access_token()
    if not token: return
    url = 'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'receive_id': receive_id, 'msg_type': 'text', 'content': json.dumps({'text': content})}
    requests.post(url, headers=headers, json=payload, timeout=10)

@app.get("/health")
async def health_check():
    return {"status": "online", "vision": "enabled", "uptime": int(time.time() - START_TIME)}

@app.post('/event')
async def handle_feishu_event(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if 'challenge' in data: return {'challenge': data['challenge']}
    
    event = data.get('event', {})
    message = event.get('message', {})
    sender = event.get('sender', {})
    open_id = sender.get('sender_id', {}).get('open_id')
    msg_type = message.get('msg_type')

    if not open_id: return {'status': 'ok'}

    image_b64 = None
    text_content = ""

    # 处理图片消息
    if msg_type == 'image':
        image_key = json.loads(message.get('content')).get('image_key')
        message_id = message.get('message_id')
        logger.info(f"[INBOUND] Image received from {open_id}")
        image_b64 = get_image_base64(message_id, image_key)
        text_content = "[图片分析请求]"
    
    # 处理文本消息
    elif msg_type == 'text':
        text_content = json.loads(message.get('content')).get('text', '').strip()
        logger.info(f"[INBOUND] Text from {open_id}: {text_content[:30]}")

    if text_content or image_b64:
        background_tasks.add_task(process_vision_and_reply, open_id, text_content, image_b64)
                
    return {'status': 'ok'}

def process_vision_and_reply(open_id, text, image_b64):
    try:
        history = session_manager.get_context(open_id)
        reply = ai_engine.ask(text, history=history, image_base64=image_b64)
        
        # 存入记忆 (如果是图片，只存入 AI 的回答和 [发送了图片] 占位符)
        session_manager.add_message(open_id, "user", text if not image_b64 else "[用户发送了图片]")
        session_manager.add_message(open_id, "assistant", reply)
        
        send_message(open_id, reply)
    except Exception as e:
        logger.error(f'[AI_CORE] Vision processing failed: {e}')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
