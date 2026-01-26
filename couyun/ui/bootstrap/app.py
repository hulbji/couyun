import json
import os

from couyun import STATE_PATH
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)

@log_exceptions
def load_state() -> dict:
    if os.path.isfile(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'is_traditional': False, 'yun_shu': 1, 'ci_pu': 1, 'bg_index': 0}

@log_exceptions
def bootstrap():
    """只做启动前准备，返回状态信息"""
    logger.info("初始化启动环境")
    current_state = load_state()
    logger.info("状态加载完成")
    return current_state
