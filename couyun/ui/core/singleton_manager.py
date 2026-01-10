import logging

class TkSingletonWindow:
    """Tkinter窗口单例管理器（适配Tk窗口生命周期）"""
    _window_instances = {}  # 缓存窗口实例：{窗口类: 实例对象}

    @classmethod
    def get_instance(cls, window_cls, *args, **kwargs):
        # 1. 检查缓存中是否有存活的实例
        if window_cls in cls._window_instances:
            instance = cls._window_instances[window_cls]
            if instance.winfo_exists():
                instance.deiconify()
                instance.lift()
                return instance
            # 实例已销毁，清除缓存
            del cls._window_instances[window_cls]

        # 2. 创建新实例并缓存
        try:
            instance = window_cls(*args, **kwargs)
            cls._window_instances[window_cls] = instance
            # 绑定关闭事件：清除缓存
            def on_close():
                if hasattr(instance, 'on_window_close'):
                    instance.on_window_close()
                if window_cls in cls._window_instances:
                    del cls._window_instances[window_cls]
            instance.protocol("WM_DELETE_WINDOW", on_close)
            return instance
        except Exception as e:
            logging.error(f"创建单例窗口 {window_cls.__name__} 失败: {e}")
            return None

    @classmethod
    def clear_instance(cls, window_cls):
        """手动清除指定窗口的单例缓存"""
        if window_cls in cls._window_instances:
            del cls._window_instances[window_cls]