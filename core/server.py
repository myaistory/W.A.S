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
from rag_engine import GroqEngine
from logger import logger  # 引入新日志模块

load_dotenv()

app = FastAPI(title='Walnut AI Support Node (LLM-Powered)')
START_TIME = time.time()
APP_ID = os.getenv('FEISHU_APP_ID')
APP_SECRET = os.getenv('FEISHU_APP_SECRET')

# 实例化 Groq 引擎
try:
    ai_engine = GroqEngine()
    logger.info('[W.A.S.] GroqEngine Loaded Successfully.')
except Exception as e:
    logger.error(f'[W.A.S.] GroqEngine Init Failed: {e}')
    ai_engine = None

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
    if not token: 
        logger.error('[FEISHU] No tenant_token available for outbound message')
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
        logger.info(f'[FEISHU] Message sent to {receive_id}. Status: {r.status_code}')
    except Exception as e:
        logger.error(f'[FEISHU] Send message failed: {e}')

@app.get("/health")
async def health_check():
    """健康检查端点 P1"""
    uptime = time.time() - START_TIME
    groq_status = "uninitialized"
    if ai_engine:
        # 简单测试一个 token 生成
        try:
            test_resp = ai_engine.ask("ping")
            groq_status = "reachable" if "[SYSTEM_ERROR]" not in test_resp else "error"
        except:
            groq_status = "down"

    return {
        "status": "online",
        "uptime_seconds": int(uptime),
        "groq_api": groq_status,
        "kb_loaded": ai_engine.kb_content != 'Knowledge base empty.' if ai_engine else False
    }

@app.post('/event')
async def handle_feishu_event(request: Request, background_tasks: BackgroundTasks):
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
            start_proc = time.time()
            content_json = json.loads(message['content'])
            text = content_json.get('text', '').strip()
            open_id = sender.get('sender_id', {}).get('open_id')
            
            if text:
                logger.info(f'[INBOUND] User:{open_id} Query:"{text[:50]}..."')
                
                if not ai_engine:
                    reply = '【系统提示】AI 核心初始化失败，请联系管理员检查 API Key。'
                    logger.warning(f'[W.A.S.] Engine unavailable for User:{open_id}')
                else:
                    # 使用背景任务异步处理 AI 逻辑，防止飞书回调超时
                    background_tasks.add_task(process_and_reply, open_id, text, start_proc)
                    
        except Exception as e:
            logger.error(f'[PROCESSOR] Internal processing error: {e}')
                
    return {'status': 'ok'}

def process_and_reply(open_id, text, start_time):
    """异步处理 AI 逻辑并回传"""
    try:
        reply = ai_engine.ask(text)
        duration = time.time() - start_time
        logger.info(f'[OUTBOUND] User:{open_id} AI_Time:{duration:.2f}s Reply:"{reply[:50]}..."')
        send_message(open_id, reply)
    except Exception as e:
        logger.error(f'[AI_CORE] Async processing failed: {e}')

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)
