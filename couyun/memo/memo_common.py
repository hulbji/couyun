def update_status(manager_or_widget, status_var, message, clear_delay=3000):

    status_var.set(message)

    if hasattr(manager_or_widget, "window"):
        widget = manager_or_widget.window
    else:
        widget = manager_or_widget

    if not hasattr(widget, "_status_clear"):
        widget._status_clear = None

    if widget._status_clear is not None:
        try:
            widget.after_cancel(widget._status_clear)
        except Exception:
            pass

    widget._status_clear = widget.after(
        clear_delay,
        lambda: status_var.set("")
    )

