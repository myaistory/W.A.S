import streamlit as st
import requests
import time
import pandas as pd

API_BASE_URL = "http://127.0.0.1:8001/api/tickets"

st.set_page_config(page_title="W.A.S. 中台", page_icon="🌰", layout="wide")

page = st.sidebar.selectbox("切换入口", ["👨‍🏫 老师提单门户", "🛠️ 二线接单后台"])

# --- 老师提单门户 ---
if page == "👨‍🏫 老师提单门户":
    st.title("核桃编程技术支持 - 提单中心")
    if "ticket_id" not in st.session_state: st.session_state.ticket_id = None

    if not st.session_state.ticket_id:
        with st.form("ticket_form"):
            teacher_id = st.text_input("老师 ID", placeholder="请输入您的工号/姓名")
            title = st.text_input("问题简述", placeholder="如：客户端打不开")
            desc = st.text_area("详情")
            if st.form_submit_button("提交并获取智能回复"):
                r = requests.post(f"{API_BASE_URL}/create", json={"user_id": teacher_id, "title": title, "description": desc})
                if r.status_code == 200:
                    st.session_state.ticket_id = r.json()["id"]
                    st.rerun()
    else:
        st.info(f"工单受理中: {st.session_state.ticket_id}")
        r = requests.get(f"{API_BASE_URL}/{st.session_state.ticket_id}")
        if r.status_code == 200:
            ticket = r.json()
            for m in ticket["messages"]:
                with st.chat_message("assistant" if m["role"] in ["ai", "admin"] else "user"):
                    st.write(f"**[{m['role'].upper()}]** {m['content']}")
        
        if st.button("问题已解决"): 
            st.session_state.ticket_id = None
            st.rerun()
        if st.button("还是不行，点此呼叫人工"):
            st.warning("已通知技术二线老师接管。")

# --- 二线接单后台 ---
else:
    st.title("W.A.S. 二线工作台")
    r = requests.get(f"{API_BASE_URL}/list")
    if r.status_code == 200:
        tickets = r.json()
        df = pd.DataFrame(tickets)
        if not df.empty:
            st.dataframe(df[["id", "user_id", "title", "status", "created_at"]], use_container_width=True)
            
            selected_id = st.selectbox("选择要接管的工单 ID", df["id"].tolist())
            if selected_id:
                t_r = requests.get(f"{API_BASE_URL}/{selected_id}")
                ticket = t_r.json()
                st.subheader(f"对话流: {ticket['title']}")
                for m in ticket["messages"]:
                    st.text(f"[{m['role']}] {m['content']}")
                
                with st.form("reply_form"):
                    reply_content = st.text_input("人工回复内容")
                    if st.form_submit_button("发送回复并结单"):
                        requests.post(f"{API_BASE_URL}/{selected_id}/respond", params={"content": reply_content})
                        st.success("回复已送达")
                        st.rerun()
        else:
            st.write("目前没有活跃工单。")
