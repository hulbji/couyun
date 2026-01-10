# couyun/bootstrap/dpi.py
import os
import ctypes
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)

@log_exceptions
def setup_dpi():
    """设置 Windows DPI 感知"""
    if os.name != 'nt':
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        logger.info("DPI 感知设置成功 (SetProcessDpiAwareness)")
    except (OSError, AttributeError, ctypes.ArgumentError) as e:
        logger.warning(f"SetProcessDpiAwareness 失败: {e}，尝试备用方法")
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            logger.info("DPI 感知设置成功 (SetProcessDPIAware)")
        except Exception as e2:
            logger.error(f"DPI 设置最终失败: {e2}")
