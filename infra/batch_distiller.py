import pandas as pd
import json
import os
import re
from core.logger import logger

def clean_text(text):
    """基础清洗：去除空白、特殊字符和脱敏处理"""
    if not isinstance(text, str):
        return ""
    # 去除换行符和多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    # 简单脱敏：隐藏手机号 (针对 11 位数字)
    text = re.sub(r'1[3-9]\d{9}', '[PHONE_HIDDEN]', text)
    return text

def distil_tickets(file_path, output_path):
    logger.info(f"[Distiller] Starting batch processing: {file_path}")
    
    try:
        # 1. 加载 Excel (由于是 4.1MB，读取可能需要几秒)
        df = pd.read_excel(file_path)
        logger.info(f"[Distiller] Loaded {len(df)} raw tickets.")

        # 2. 字段映射与过滤 (根据常见工单结构猜测字段名，并在下方进行适配)
        # 常见核桃工单字段推测: '问题描述', '解决方案', '工单状态'
        # 我们先列出所有列名以便调试
        logger.info(f"[Distiller] Columns found: {df.columns.tolist()}")

        # 尝试寻找关键列
        desc_col = next((c for c in df.columns if '描述' in c or '内容' in c or 'Description' in c), None)
        sol_col = next((c for c in df.columns if '方案' in c or '解决' in c or 'Solution' in c), None)
        status_col = next((c for c in df.columns if '状态' in c or 'Status' in c), None)

        if not desc_col or not sol_col:
            logger.error("[Distiller] Required columns (Description/Solution) not found in Excel.")
            return

        # 3. 筛选已解决的工单
        if status_col:
            df = df[df[status_col].astype(str).str.contains('已解决|已关闭|Finished|Closed', na=False)]
            logger.info(f"[Distiller] Filtered resolved tickets: {len(df)}")

        knowledge_base = []
        seen_questions = set()

        # 4. 遍历提取
        for _, row in df.iterrows():
            question = clean_text(row[desc_col])
            answer = clean_text(row[sol_col])

            if len(question) < 5 or len(answer) < 5:
                continue

            # 简易去重逻辑：如果问题前 20 个字完全一样，视为重复
            q_fingerprint = question[:20]
            if q_fingerprint in seen_questions:
                continue
            
            seen_questions.add(q_fingerprint)

            knowledge_base.append({
                "title": question[:50],  # 提取前50字作为标题
                "content": f"问题现象: {question}\n解决方案: {answer}"
            })

        # 5. 保存为 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

        logger.info(f"[Distiller] Success! Distilled {len(knowledge_base)} high-quality SOPs into {output_path}")

    except Exception as e:
        logger.error(f"[Distiller] Batch processing failed: {e}")

if __name__ == "__main__":
    RAW_PATH = "/home/lianwei_zlw/Walnut-AI-Support/data/raw_tickets.xlsx"
    OUT_PATH = "/home/lianwei_zlw/Walnut-AI-Support/data/walnut_kb.json"
    distil_tickets(RAW_PATH, OUT_PATH)
