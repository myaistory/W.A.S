import logging
import os
from logging.handlers import RotatingFileHandler

# 确保日志目录存在
LOG_DIR = "/home/lianwei_zlw/Walnut-AI-Support/logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name="WAS"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # 格式化器：时间 - 级别 - 消息
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 文件滚动：每个文件10MB，保留5个备份
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, "was.log"), 
            maxBytes=10*1024*1024, 
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # 同时输出到控制台（方便 nohup 查看）
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

logger = get_logger()
