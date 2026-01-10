import json
import os

# from couyun.ui.memo_interface import RhythmCheckerGUI
# from couyun.ui.utils.scaling import scaled_tk_value
from couyun import STATE_PATH
from couyun.ui.bootstrap.dpi import setup_dpi
from couyun.ui.bootstrap.singleton import ensure_single_instance
# from couyun.ui.state.state_manager import load_state
from couyun.ui.core.logger_config import get_logger, log_exceptions

# from couyun.ui.assets.font_loader import load_font, FONT_PATH
# from couyun.ui.memo_interface import on_close

logger = get_logger(__name__)

def load_state() -> dict:
    if os.path.isfile(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'is_traditional': False, 'yun_shu': 1, 'ci_pu': 1, 'bg_index': 0}

@log_exceptions
def bootstrap():
    """只做启动前准备，返回状态信息"""
    logger.info("初始化启动环境")
    setup_dpi()
    current_state = load_state()
    logger.info("状态加载完成")
    window_title = "湊韻" if current_state.get('is_traditional', False) else "凑韵"
    ensure_single_instance(window_title)
    logger.info("tesssssst")
    return current_state
