from PyQt6.QtCore import QSharedMemory, QObject
from PyQt6.QtNetwork import QLocalServer


class SingleInstance(QObject):
    def __init__(self, key: str):
        super().__init__()
        self.key = key
        self.shared = QSharedMemory(key)
        self.server = None

    def is_running(self) -> bool:
        # 如果能 attach，说明已有实例
        if self.shared.attach():
            self.shared.detach()
            return True

        # 否则创建共享内存
        if not self.shared.create(1):
            return True

        # 创建本地服务器（用于激活已有实例等扩展）
        self.server = QLocalServer()
        self.server.removeServer(self.key)
        self.server.listen(self.key)
        return False
