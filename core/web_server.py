from fastapi import APIRouter, HTTPException, BackgroundTasks
from core.models import Ticket, TicketCreate, TicketStatus, Message, Role
from core.rag_engine import ai_engine
from core.logger import logger
import uuid
import sqlite3
import json
from datetime import datetime
from typing import List, Optional

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

DB_PATH = "data/sessions.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tickets 
                     (id TEXT PRIMARY KEY, user_id TEXT, category TEXT, title TEXT, 
                      description TEXT, status TEXT, messages TEXT, created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@router.post("/create", response_model=Ticket)
async def create_ticket(data: TicketCreate, background_tasks: BackgroundTasks):
    ticket_id = str(uuid.uuid4())[:8]
    new_ticket = Ticket(
        id=ticket_id,
        user_id=data.user_id,
        category=data.category or "自动识别",
        title=data.title,
        description=data.description,
        status=TicketStatus.AI_PROCESSING,
        messages=[Message(role=Role.USER, content=data.description)]
    )
    
    save_ticket(new_ticket)
    logger.info(f"[WEB_TICKET] Created: {ticket_id}")
    background_tasks.add_task(ai_diagnostic_process, ticket_id)
    return new_ticket

@router.get("/list", response_model=List[Ticket])
async def list_tickets(status: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM tickets ORDER BY created_at DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    tickets = []
    for row in rows:
        tickets.append(Ticket(
            id=row[0], user_id=row[1], category=row[2], title=row[3],
            description=row[4], status=TicketStatus(row[5]),
            messages=json.loads(row[6]), created_at=datetime.fromisoformat(row[7])
        ))
    return tickets

@router.post("/{ticket_id}/respond")
async def admin_respond(ticket_id: str, content: str):
    """二线人工回复接口"""
    ticket = get_ticket_from_db(ticket_id)
    if not ticket: raise HTTPException(404)
    
    msg = Message(role=Role.ADMIN, content=content)
    ticket.messages.append(msg)
    ticket.status = TicketStatus.RESOLVED # 暂时简化逻辑
    save_ticket(ticket)
    return {"status": "ok"}

def save_ticket(ticket: Ticket):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tickets VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (ticket.id, ticket.user_id, ticket.category, ticket.title, 
                    ticket.description, ticket.status.value, 
                    json.dumps([m.dict() for m in ticket.messages], default=str),
                    ticket.created_at.isoformat()))
    conn.commit()
    conn.close()

def get_ticket_from_db(ticket_id: str) -> Optional[Ticket]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    return Ticket(
        id=row[0], user_id=row[1], category=row[2], title=row[3],
        description=row[4], status=TicketStatus(row[5]),
        messages=json.loads(row[6]), created_at=datetime.fromisoformat(row[7])
    )

async def ai_diagnostic_process(ticket_id: str):
    """AI 自动化诊断逻辑：具备自动转人工能力"""
    ticket = get_ticket_from_db(ticket_id)
    if not ticket: return
    try:
        # 调用 RAG 引擎获取回复
        ai_reply = ai_engine.ask(f"问题:{ticket.title} 描述:{ticket.description}")
        
        # 1. 自动转人工判断逻辑：如果检索结果为 NO_MATCH 或 AI 明确回复不知道
        if "很抱歉" in ai_reply or "尚未收录" in ai_reply or "NO_MATCH" in ai_reply:
            ticket.status = TicketStatus.HUMAN_NEEDED
            ticket.messages.append(Message(role=Role.AI, content="[系统通知] AI 无法从现有知识库找到解决方案，正在为您自动转接二线技术支持..."))
            logger.info(f"[AUTO_ESCALATE] Ticket {ticket_id} escalated due to knowledge gap.")
        else:
            ticket.messages.append(Message(role=Role.AI, content=ai_reply))
            # AI 成功匹配后，状态依然保持 AI_PROCESSING，直到用户确认或 AI 无法继续
            
        save_ticket(ticket)
        
    except Exception as e:
        logger.error(f"AI Process failed: {e}")
        # 如果推理出错，也强制转人工，防止流程阻塞
        ticket.status = TicketStatus.HUMAN_NEEDED
        ticket.messages.append(Message(role=Role.AI, content="[系统错误] 推理核心暂不可用，已为您自动转接人工。"))
        save_ticket(ticket)
