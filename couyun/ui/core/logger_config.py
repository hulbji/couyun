import logging
import logging.handlers
import traceback
import os
from functools import wraps

UI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(UI_DIR, 'assets', 'state')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_root_logger():
    """配置根日志器，仅执行一次"""
    root_logger = logging.getLogger("RhythmChecker")
    if not getattr(root_logger, "_configured", False):
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.DEBUG)
        root_logger._configured = True  # 防止重复配置

    return root_logger

def get_logger(name=None) -> logging.Logger:
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    setup_root_logger()
    return logging.getLogger(f"RhythmChecker.{name.split('.')[-1]}")

def log_exceptions(func):
    """自动记录函数/方法执行情况和异常的装饰器"""
    original_name = func.__name__

    @wraps(func)
    def wrapper(*args, **kwargs):
        if args and hasattr(args[0], '__class__'):
            logger = get_logger(args[0].__class__.__name__)
        else:
            logger = get_logger(func.__module__)
        func_name = original_name
        try:
            result = func(*args, **kwargs)
            logger.info(f"【{func_name}】正常完成")
            for h in logger.handlers:  # flush日志
                h.flush()
            return result
        except Exception as error:
            logger.error(f"【{func_name}】发生异常: {str(error)}")
            logger.error(traceback.format_exc())
            for h in logger.handlers:
                h.flush()
            raise
    return wrapper

setup_root_logger()
