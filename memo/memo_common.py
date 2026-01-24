# memo_common.py
from PyQt6.QtCore import QTimer


def update_status(widget, status_label, message, clear_delay=3000):
    """
    PyQt6 版本的状态栏更新函数

    Args:
        widget: 拥有定时器的父组件（通常是 QMainWindow）
        status_label: 要更新的 QLabel 对象
        message: 要显示的消息文本
        clear_delay: 自动清除延迟（毫秒）
    """
    if not status_label:
        return

    # 确保 widget 有定时器存储属性
    if not hasattr(widget, "_status_clear_timer"):
        widget._status_clear_timer = None

    # 取消之前的定时器
    if widget._status_clear_timer is not None:
        try:
            widget._status_clear_timer.stop()
            widget._status_clear_timer.deleteLater()
        except Exception:
            pass

    # 设置新消息
    status_label.setText(message)

    # 如果消息非空，设置自动清除
    if message:
        widget._status_clear_timer = QTimer(widget)
        widget._status_clear_timer.setSingleShot(True)
        widget._status_clear_timer.timeout.connect(lambda: status_label.setText(""))
        widget._status_clear_timer.start(clear_delay)