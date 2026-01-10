# couyun/bootstrap/singleton.py
import sys
import ctypes
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)

_MUTEX_NAME = "RhythmChecker"
_ERROR_ALREADY_EXISTS = 183

@log_exceptions
def ensure_single_instance(window_title: str):
    """
    确保程序单实例运行。
    若已存在实例，则尝试激活已有窗口并退出当前进程。
    """
    kernel32 = ctypes.windll.kernel32
    # handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    last_error = kernel32.GetLastError()

    if last_error == _ERROR_ALREADY_EXISTS:
        logger.warning("检测到程序已在运行，尝试激活已有窗口...")
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 5)   # SW_SHOW
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                logger.info("已激活已有窗口，当前实例将退出")
            else:
                logger.warning("未找到已有窗口句柄")
        except Exception as e:
            logger.error(f"激活已有窗口失败: {e}")
        sys.exit(0)

    logger.info("单实例检测通过")
