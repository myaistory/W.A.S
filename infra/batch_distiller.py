import pandas as pd
import json
import os
import re
import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        desc_col = '问题现象' # 根据日志修正
        sol_col = '解决方式'  # 根据日志修正
        status_col = None     # 该表似乎没有状态列，或者状态隐含在解决方式中

        if desc_col not in df.columns or sol_col not in df.columns:
            logger.error(f"[Distiller] Required columns {desc_col}/{sol_col} not found.")
            return

        knowledge_base = []
        seen_questions = set()

        # 4. 遍历提取
        for _, row in df.iterrows():
            question = clean_text(row[desc_col])
            answer = clean_text(row[sol_col])
            
            # 强化清洗：过滤掉太短或明显无意义的回答
            if len(str(question)) < 4 or len(str(answer)) < 4:
                continue
            
            # 过滤掉全横杠或全符号的噪音
            if re.match(r'^[_\-\s\./\\]+$', str(question)) or re.match(r'^[_\-\s\./\\]+$', str(answer)):
                continue
            
            if '测试' in str(question) or 'test' in str(question).lower():
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
