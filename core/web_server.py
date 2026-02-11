from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.models import Ticket, TicketCreate, TicketStatus, Message, Role
from core.rag_engine import ai_engine
from core.logger import logger
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

# 内存暂存池 (后期迁移到 PostgreSQL)
TICKET_DB = {}

@router.post("/create", response_model=Ticket)
async def create_ticket(data: TicketCreate, background_tasks: BackgroundTasks):
    """网页端提单入口"""
    ticket_id = str(uuid.uuid4())[:8]
    
    # 初始化工单
    new_ticket = Ticket(
        id=ticket_id,
        user_id=data.user_id,
        category=data.category,
        title=data.title,
        description=data.description
    )
    
    # 记录初始消息
    new_ticket.messages.append(Message(role=Role.USER, content=data.description))
    TICKET_DB[ticket_id] = new_ticket
    
    logger.info(f"[WEB_TICKET] Created: {ticket_id} - {data.title}")
    
    # 异步触发 AI 诊断
    background_tasks.add_task(ai_diagnostic_process, ticket_id)
    
    return new_ticket

@router.get("/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    if ticket_id not in TICKET_DB:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TICKET_DB[ticket_id]

async def ai_diagnostic_process(ticket_id: str):
    """AI 自动化排查逻辑"""
    ticket = TICKET_DB.get(ticket_id)
    if not ticket: return

    try:
        # 调用 RAG 引擎
        ai_reply = ai_engine.ask(f"类别:{ticket.category} 标题:{ticket.title} 问题:{ticket.description}")
        
        # 记录 AI 回复
        ticket.messages.append(Message(role=Role.AI, content=ai_reply))
        ticket.updated_at = datetime.now()
        
        logger.info(f"[AI_DIAGNOSTIC] Ticket {ticket_id} processed by AI.")
    except Exception as e:
        logger.error(f"[AI_DIAGNOSTIC] Failed for {ticket_id}: {e}")

# 集成到主应用逻辑在 server.py 中完成
