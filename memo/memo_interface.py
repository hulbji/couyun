import json
import os
from datetime import datetime

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, \
    QStatusBar, QDialog, QFrame, QMessageBox, QStackedWidget

# from couyun.memo.memo_category import CategoryManager
# from couyun.memo.memo_common import update_status
# from couyun.memo.memo_export import ExportManager
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)

# noinspection PyTypeChecker
class MemoInterface(QMainWindow):
    def __init__(self, parent, fonts, resource_path, is_trad):

        self.widgets_to_translate = []
        self.s2t = str.maketrans(
            "个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
            "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验",
            "个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
            "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗")
        self.t2s = str.maketrans(
            "个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
            "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗",
            "个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
            "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验")
        super().__init__(parent)

        self.fonts = fonts
        self.resource_path = resource_path
        self.is_trad = is_trad
        self.parent = parent

        self.data_path = os.path.join(os.path.dirname(resource_path()), './assets/state/memo_data.json')

        self.setWindowTitle("備忘錄" if is_trad else "备忘录")
        self.resize(1000, 800)
        self.setFixedSize(1000, 800)

        self.notes = []
        self.categories = ["诗词", "摘抄"]
        self.default_category = "诗词"
        self.current_filter = "全部"
        self.search_keyword = ""
        self.sort_mode = "时间倒序"
        self.current_displayed_notes = []

        self.selected_ids = set()
        self.export_path = os.getcwd()
        self.validate_choice_window = None

        self.current_note_id = None
        # self.status_var = None
        self.toggle_btn = None
        self.content_text = None
        self.category_var = None
        self.title_var = None
        self.detail_frame = None
        self.notes_listbox = None
        self.sort_var = None
        self.filter_var = None
        self.search_var = None
        self.main_frame = None
        self.status_clear_timer = None
        self.status_label = None
        self.status_bar = None
        self.detail_layout = None
        self.main_layout = None
        self.stacked_widget = None

        self.load_data()
        self.create_ui()
        # self.show_list_view()
        QTimer.singleShot(0, self._post_ui_init)

        # self.destroyed.connect(self.on_window_close)

    @ log_exceptions
    def _post_ui_init(self):
        """
        UI 已经显示后，再执行的慢操作
        """
        self.refresh_notes_list()
        self.update_status("")

    def memo_register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    @log_exceptions
    def toggle_language(self):
        """在简体和繁体之间切换（注意：使用目标模式来渲染）"""
        to_trad = not self.is_trad  # 目标模式

        for widget in self.widgets_to_translate:
            try:
                if widget:
                    # PyQt6 控件的 text 获取和设置
                    if hasattr(widget, 'text') and callable(widget.text):
                        orig = widget.text()
                        new_text = self.cc_convert(orig, to_trad)
                        widget.setText(new_text)
                    # QTextEdit 等文本控件
                    elif hasattr(widget, 'toPlainText') and callable(widget.toPlainText):
                        orig = widget.toPlainText()
                        new_text = self.cc_convert(orig, to_trad)
                        widget.setPlainText(new_text)
            except Exception:
                continue

        title_text = "備忘錄" if to_trad else "备忘录"
        self.setWindowTitle(title_text)
        btn_text = '繁體' if not to_trad else '简体'
        if self.toggle_btn:
            self.toggle_btn.setText(btn_text)
        self.is_trad = to_trad

    @log_exceptions
    def cc_convert(self, text, to_trad: bool):
        """根据目标模式转换文本"""
        return text.translate(self.s2t) if to_trad else text.translate(self.t2s)

    @log_exceptions
    def create_ui(self):
        """UI 总入口，使用 QStackedWidget 管理多界面"""
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.create_main_ui()
        self.create_detail_ui()
        self.create_status_bar()  # 必须在 addWidget 之前调用

        self.stacked_widget.addWidget(self.main_frame)
        self.stacked_widget.addWidget(self.detail_frame)

        self.show_list_view()

    @log_exceptions
    def create_main_ui(self):
        """备忘录主界面（PyQt6版）"""
        self.main_frame = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_frame)
        self.main_frame.setLayout(self.main_layout)
        # 删除 self.setCentralWidget(self.main_frame)，由 QStackedWidget 管理

    @log_exceptions
    def create_detail_ui(self):
        """笔记详情 / 编辑界面（PyQt6版）"""
        self.detail_frame = QWidget(self)
        self.detail_layout = QVBoxLayout(self.detail_frame)
        self.detail_frame.setLayout(self.detail_layout)
        # 删除 self.setCentralWidget(self.detail_frame)，由 QStackedWidget 管理

    @log_exceptions
    def create_status_bar(self):
        """创建状态栏（PyQt6 版，带自动清除）"""
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # 存储为实例变量，确保可在类方法中访问
        self.status_label = QLabel(self.status_bar)
        self.status_label.setFont(self.fonts['small'])
        self.status_bar.addWidget(self.status_label)
        self.status_label.setText("")  # 初始为空

    @log_exceptions
    def update_status(self, message, clear_delay=3000):
        """
        更新状态栏文本，并在指定毫秒后自动清除

        Args:
            message: 要显示的消息
            clear_delay: 自动清除延迟（毫秒），默认 3000ms
        """
        if not hasattr(self, 'status_label') or not self.status_label:
            return

        # 取消之前的定时器
        if self.status_clear_timer is not None:
            try:
                self.status_clear_timer.stop()
                self.status_clear_timer.deleteLater()
            except Exception:
                pass

        # 设置新消息
        self.status_label.setText(message)

        # 如果消息非空，设置自动清除
        if message:
            self.status_clear_timer = QTimer(self)
            self.status_clear_timer.setSingleShot(True)
            self.status_clear_timer.timeout.connect(lambda: self.status_label.setText(""))
            self.status_clear_timer.start(clear_delay)

    @log_exceptions
    def open_validate_choice(self):
        """打开校验选择窗口（PyQt6版）"""
        if self.validate_choice_window is not None and self.validate_choice_window.isVisible():
            self.validate_choice_window.raise_()
            return

        self.validate_choice_window = QDialog(self)
        self.validate_choice_window.setWindowTitle("選擇校驗類型" if self.is_trad else "选择校验类型")
        self.validate_choice_window.setFixedSize(300, 200)
        self.validate_choice_window.setModal(True)  # 模态窗口

        # 窗口关闭时清空引用
        self.validate_choice_window.finished.connect(lambda: setattr(self, 'validate_choice_window', None))

        frame = QFrame(self.validate_choice_window)
        layout = QVBoxLayout(frame)
        frame.setLayout(layout)
        frame.setContentsMargins(20, 20, 20, 20)

        poem_btn = QPushButton("🔍 校驗詩" if self.is_trad else "🔍 校验诗", frame)
        poem_btn.setFont(self.fonts['default'])
        poem_btn.setFixedWidth(150)
        poem_btn.setStyleSheet("background-color: #c9a6eb;")
        poem_btn.clicked.connect(lambda: self.execute_validate('poem'))
        layout.addWidget(poem_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        ci_btn = QPushButton("🔍 校驗詞" if self.is_trad else "🔍 校验词", frame)
        ci_btn.setFont(self.fonts['default'])
        ci_btn.setFixedWidth(150)
        ci_btn.setStyleSheet("background-color: #c9a6eb;")
        ci_btn.clicked.connect(lambda: self.execute_validate('ci'))
        layout.addWidget(ci_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.validate_choice_window.show()

    def execute_validate(self, mode):
        """执行校验"""
        """
        content = self.content_text.get("1.0", tk.END).strip()
        self.parent.validate_content(mode, content)
        self.validate_choice_window.destroy()"""
        pass

    def show_list_view(self):
        """显示主列表界面（PyQt6版）"""
        self.stacked_widget.setCurrentWidget(self.main_frame)
        self.refresh_notes_list()
        self.update_status("")

    def show_detail_view(self):
        """显示详情编辑界面（PyQt6版）"""
        self.stacked_widget.setCurrentWidget(self.detail_frame)
        # 设置内部布局的边距
        if hasattr(self.detail_frame, 'layout'):
            self.detail_frame.layout().setContentsMargins(20, 20, 20, 20)

    def show_new_note_view(self):
        """新建笔记时调用（PyQt6版）"""
        self.current_note_id = None
        if self.title_var:
            self.title_var.setText("")
        if self.content_text:
            self.content_text.clear()
        if self.category_var:
            self.category_var.setCurrentText(self.default_category)

        self.show_detail_view()

    def load_data(self):
        """从JSON文件加载数据"""
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.notes = data.get('notes', [])
                self.categories = data.get('categories', ["诗词", "摘抄"])
                self.default_category = data.get('default_category', "诗词")
                self.export_path = data.get('export_path', os.getcwd())
                if self.default_category not in self.categories:
                    self.categories.insert(0, self.default_category)
        else:
            self.notes = []
            self.categories = ["诗词", "摘抄"]
            self.default_category = "诗词"
            self.export_path = os.getcwd()
            self.save_data()

    @log_exceptions
    def save_data(self):
        """保存数据到JSON文件"""
        data = {
            'notes': self.notes,
            'categories': self.categories,
            'default_category': self.default_category,
            'export_path': self.export_path  # 保存导出路径
        }
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @log_exceptions
    def save_current_note(self):
        """手动保存当前编辑的笔记（PyQt6版）"""
        title = self.title_var.text().strip() if self.title_var else ""
        content = self.content_text.toPlainText().strip() if self.content_text else ""
        category = self.category_var.currentText().strip() if self.category_var else self.default_category
        if not category:
            category = self.default_category

        if not title and not content:
            self.update_status("筆記為空，未保存" if self.is_trad else "笔记为空，未保存")
            return

        now_iso = datetime.now().isoformat()
        if self.current_note_id is None:
            new_note = {
                'id': str(datetime.now().timestamp()),
                'title': title or "NoName",
                'content': content,
                'category': category,
                'created_time': now_iso,
                'modified_time': now_iso
            }
            self.notes.append(new_note)
            self.current_note_id = new_note['id']
            self.update_status("新建筆記已保存" if self.is_trad else "新建笔记已保存")
        else:
            for note in self.notes:
                if note['id'] == self.current_note_id:
                    note['title'] = title or note['title']
                    note['content'] = content
                    note['category'] = category
                    note['modified_time'] = now_iso
                    break
            self.update_status("筆記已保存" if self.is_trad else "笔记已保存")

        self.save_data()
        self.refresh_notes_list()

    @log_exceptions
    def delete_note(self):
        """删除当前笔记（PyQt6版）"""
        if not self.current_note_id:
            return

        msg = "確定要刪除這條筆記嗎？" if self.is_trad else "确定要删除这条笔记吗？"
        title = "確認刪除" if self.is_trad else "确认删除"

        reply = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.notes = [n for n in self.notes if n['id'] != self.current_note_id]
            self.save_data()
            self.current_note_id = None
            self.show_list_view()
            self.update_status("筆記已刪除" if self.is_trad else "笔记已删除")

    @log_exceptions
    def on_note_select(self, _=None):
        """双击笔记打开详情（PyQt6版）"""
        index = self.notes_listbox.currentRow()
        if index < 0 or index >= len(self.current_displayed_notes):
            return

        note = self.current_displayed_notes[index]
        self.current_note_id = note['id']

        if self.title_var:
            self.title_var.setText(note['title'])
        if self.content_text:
            self.content_text.setPlainText(note['content'])
        if self.category_var:
            self.category_var.setCurrentText(note['category'])

        self.show_detail_view()

    @log_exceptions
    def on_search(self, _):
        """搜索事件"""
        self.search_keyword = self.search_var.get().strip().lower()
        self.refresh_notes_list()

    @log_exceptions
    def on_filter_change(self, _):
        """筛选变化事件"""
        self.current_filter = self.filter_var.get()
        self.refresh_notes_list()

    @log_exceptions
    def on_sort_change(self, _):
        """排序变化事件"""
        self.sort_mode = self.sort_var.get()
        self.refresh_notes_list()

    @log_exceptions
    def on_listbox_click(self, event):
        """处理列表点击事件，空白区域不选中最后一个项目（PyQt6版）"""
        item = self.notes_listbox.itemAt(event.pos())
        if item is None:
            self.notes_listbox.clearSelection()
            return

    @log_exceptions
    def get_filtered_notes(self):
        """获取筛选后的笔记"""
        filtered = self.notes
        if self.search_keyword:
            filtered = [n for n in filtered if self.search_keyword in n['title'].lower() or
                        self.search_keyword in n['content'].lower()]
        if self.current_filter != "全部":
            filtered = [n for n in filtered if n['category'] == self.current_filter]
        return filtered

    @log_exceptions
    def sort_notes(self, notes):
        """排序笔记"""
        if self.sort_mode in ["时间倒序", "時間倒序"]:
            return sorted(notes, key=lambda x: x['modified_time'], reverse=True)
        elif self.sort_mode in ["时间正序", "時間正序"]:
            return sorted(notes, key=lambda x: x['modified_time'])
        elif self.sort_mode in ["标题", "標題"]:
            return sorted(notes, key=lambda x: x['title'])
        elif self.sort_mode in ["类型", "類型"]:
            return sorted(notes, key=lambda x: (x['category'], x['title']))
        return None

    @log_exceptions
    def refresh_notes_list(self):
        """刷新笔记列表显示（PyQt6版）"""
        if not self.notes_listbox:
            return

        self.notes_listbox.clear()
        notes = self.get_filtered_notes()
        notes = self.sort_notes(notes)

        self.current_displayed_notes = notes

        for note in notes:
            display_text = f"{note['title'][:35]} | {note['category']} | {note['modified_time'][:10]}"
            self.notes_listbox.addItem(display_text)

    '''    @log_exceptions
    def open_category_manager(self):
        """打开分类管理窗口（模态），关闭后统一刷新主界面"""

        mgr = CategoryManager(
            parent=self,
            notes=self.notes,
            categories=self.categories,
            default_category=self.default_category,
            fonts=self.fonts,
            is_trad=self.is_trad
        )
        mgr.window.exec()  # PyQt6 模态对话框执行方式

        if mgr.dirty:
            self.default_category = mgr.default_category
            self.categories = mgr.categories
            self.notes = mgr.notes

            self.refresh_notes_list()
            self.save_data()

            self.update_status("分类已更新" if not self.is_trad else "類型已更新")

    @log_exceptions
    def open_export_manager(self):
        """打开导出管理窗口（模态），关闭后统一处理"""

        mgr = ExportManager(
            parent=self,
            notes=self.notes,
            categories=self.categories,
            export_path=self.export_path,
            fonts=self.fonts,
            is_trad=self.is_trad
        )
        mgr.window.exec()  # PyQt6 模态对话框执行方式

        self.update_status(f"已导出笔记到: {mgr.export_path}")
        self.export_path = mgr.export_path'''

    @log_exceptions
    def closeEvent(self, event):
        """重写关闭事件，保存数据并清理资源"""
        try:
            # 保存未保存的内容
            if not self.current_note_id:
                title = self.title_var.text().strip() if self.title_var else ""
                content = self.content_text.toPlainText().strip() if self.content_text else ""
                if title or content:
                    category = self.category_var.currentText().strip() if self.category_var else self.default_category
                    new_note = {
                        'id': str(datetime.now().timestamp()),
                        'title': title or "NoName",
                        'content': content,
                        'category': category,
                        'created_time': datetime.now().isoformat(),
                        'modified_time': datetime.now().isoformat()
                    }
                    self.notes.append(new_note)

            # 清理单例引用
            if hasattr(MemoInterface, '_instance'):
                MemoInterface._instance = None

            # 保存数据
            self.save_data()
            event.accept()

        except Exception as e:
            logger.error(f"关闭窗口时发生错误: {e}")
            event.accept()  # 即使出错也要关闭
