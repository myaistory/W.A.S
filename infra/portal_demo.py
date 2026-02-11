import streamlit as st
import requests
import json
import time

# 配置
API_BASE_URL = "http://127.0.0.1:8001/api/tickets"

st.set_page_config(page_title="核桃技术支持 - 工单门户", page_icon="🌰", layout="centered")

st.title("🌰 核桃编程技术支持工单中心")
st.markdown("---")

# 初始化 Session State
if "ticket_id" not in st.session_state:
    st.session_state.ticket_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 步骤 1: 提单界面
if not st.session_state.ticket_id:
    st.header("📝 提交新问题")
    with st.form("ticket_form"):
        teacher_id = st.text_input("老师 ID (或姓名)", placeholder="请输入您的 ID")
        title = st.text_input("问题简述", placeholder="例如：双击图标没反应")
        description = st.text_area("详细描述", placeholder="请描述具体表现，如有报错代码请填写...")
        
        submit_btn = st.form_submit_button("发起智能诊断")

        if submit_btn:
            if not teacher_id or not title or not description:
                st.error("请完整填写所有必填项")
            else:
                # 调用后端 API
                payload = {
                    "user_id": teacher_id,
                    "category": "自动识别",
                    "title": title,
                    "description": description
                }
                try:
                    r = requests.post(f"{API_BASE_URL}/create", json=payload)
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.ticket_id = data["id"]
                        st.session_state.chat_history.append({"role": "user", "content": description})
                        st.rerun()
                    else:
                        st.error("后台服务连接失败")
                except Exception as e:
                    st.error(f"连接异常: {e}")

# 步骤 2: 诊断与交互界面
else:
    st.success(f"工单已受理 - ID: {st.session_state.ticket_id}")
    
    # 刷新并获取 AI 回复
    with st.spinner("AI 正在匹配 SOP 库..."):
        time.sleep(2) # 等待异步任务处理
        r = requests.get(f"{API_BASE_URL}/{st.session_state.ticket_id}")
        if r.status_code == 200:
            ticket_data = r.json()
            st.session_state.chat_history = ticket_data["messages"]

    # 展示对话
    for msg in st.session_state.chat_history:
        with st.chat_message("assistant" if msg["role"] == "ai" else "user"):
            st.write(msg["content"])

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 已解决，点此结单"):
            st.balloons()
            st.success("感谢您的反馈！本工单已关闭。")
            if st.button("回到首页"):
                st.session_state.ticket_id = None
                st.rerun()
    with col2:
        if st.button("❌ 没用，呼叫二线人工"):
            st.warning("已通知二线技术值班老师。请保持飞书或网页在线，老师将稍后接入。")
            # 这里可以触发一个飞书警报
            st.info("人工受理中...")

    if st.button("⬅️ 返回提单页"):
        st.session_state.ticket_id = None
        st.rerun()
