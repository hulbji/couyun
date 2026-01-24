import json
import os

from PyQt6 import sip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QListWidget,
    QLineEdit, QPushButton, QCheckBox, QFrame, QTextEdit, QApplication)

from couyun import CI_TRAD, CI_LONG_TRAD, CI_ORIGIN, CI_LONG_ORIGIN, bg_pic, ICO_PATH
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)


def load_ci_index(json_path):
    """读取列表形式的 ci_index（每项为 {'name': [...], 'type': [...] }）"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class CiPuBrowser(QWidget):
    _instance = None
    def __init__(self, parent, json_path, fonts, state):
        super().__init__(parent)
        CiPuBrowser._instance = self

        # ===== 关键：设置为独立窗口 =====
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # ===== 状态与数据 =====
        self.is_trad = state.get('is_trad', False)
        self.current_state = state
        self.fonts = fonts
        self.sort_mode = state['sort_mode']
        self.indexed = load_ci_index(json_path)
        self.long_only_idx = {1, 10, 11, 22, 23, 24, 28, 29, 36, 47, 50, 52, 54, 57, 58, 60, 62, 64, 65, 67, 69, 74, 75,
                              79, 81, 85, 86, 90, 91, 96, 102, 104, 105, 106, 109, 110, 113, 116, 126, 127, 128, 129,
                              133, 138, 141, 145, 149, 150, 151, 157, 158, 161, 162, 175, 181, 183, 186, 187, 190, 225,
                              226, 246, 247, 253, 260, 261, 262, 268, 271, 275, 289, 294, 295, 304, 313, 316, 325, 326,
                              328, 329, 341, 343, 345, 348, 349, 350, 355, 372, 381, 389, 406, 410, 413, 422, 430, 437,
                              438, 446, 471, 473, 476, 483, 485, 494, 499, 504, 516, 518, 528, 529, 531, 533, 543, 545,
                              546, 553, 562, 578, 580, 590, 598, 612, 614, 616, 617, 621, 625, 634, 637, 638, 649, 650,
                              652, 658, 660, 662, 664, 667, 668, 678, 688, 697, 698, 706, 722, 728, 730, 738, 742, 765,
                              775, 781, 782, 795, 798, 800, 802, 804, 805, 806, 811, 812, 814}

        self.current_show = 'qin'
        self.current_item = None
        self.current_matched = []

        # ===== 窗口属性 =====
        self.setWindowTitle("詞譜查詢" if self.is_trad else "词谱查询")
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        screen_width, screen_height = screen_size.width(), screen_size.height()

        win_width = int(screen_width * 0.65)
        win_height = int(win_width * 3 / 4)  # 4:3
        self.setFixedSize(win_width, win_height)

        self.setWindowIcon(QIcon(ICO_PATH))

        # ===== 背景 =====
        img_path = bg_pic(state.get('bg_index', 0))

        pix = QPixmap(img_path).scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.bg_label = QLabel(self)
        self.bg_label.setPixmap(pix)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.lower()

        # ===== 灰色背景样式 =====
        self.gray_style = "background-color: rgba(50, 50, 50, 150); color: white; padding: 5px 8px; border-radius: 3px;"

        # ===== 主框架 =====
        # 宽度95%，高度上方留5%、下方留10%
        main_frame_width = int(self.width() * 0.95)
        main_frame_height = int(self.height() * 0.85)  # 100% - 5% - 10%
        main_frame_x = (self.width() - main_frame_width) // 2  # 水平居中
        main_frame_y = int(self.height() * 0.05)  # 上方留5%

        self.main_frame = QFrame(self)
        self.main_frame.setGeometry(main_frame_x, main_frame_y,
                                    main_frame_width, main_frame_height)

        main_layout = QVBoxLayout(self.main_frame)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ===== 搜索栏 =====
        search_layout = QHBoxLayout()
        search_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 左对齐

        self.search_hint = QLabel("輸入詞譜名/拼音：" if self.is_trad else "输入词谱名/拼音：")
        self.search_hint.setFont(fonts['default'])
        self.search_hint.setStyleSheet(self.gray_style)

        self.search_var = QLineEdit()
        self.search_var.setFont(fonts['default'])
        self.search_var.setFixedWidth(200)  # 固定宽度，更紧凑
        self.search_var.textChanged.connect(lambda: self.update_list())

        search_layout.addWidget(self.search_hint)
        search_layout.addWidget(self.search_var)
        search_layout.addStretch()  # 右侧填充，保持左对齐效果
        main_layout.addLayout(search_layout)

        # ===== 列表区 =====
        self.result_box = QListWidget()
        self.result_box.setFont(fonts['small'])
        self.result_box.itemDoubleClicked.connect(lambda: self.open_detail())
        # 设置更紧凑的列表项高度
        self.result_box.setStyleSheet("""
            QListWidget::item { 
                height: 20px; 
                padding: 2px;
            }
        """)
        main_layout.addWidget(self.result_box)

        # ===== 无结果提示 =====
        self.no_result_label = QLabel("")
        self.no_result_label.setFont(fonts['default'])
        self.no_result_label.setStyleSheet(self.gray_style)
        self.no_result_label.hide()  # 初始隐藏
        main_layout.addWidget(self.no_result_label)

        # ===== 底部按钮区域 =====
        self.bottom_bar = QFrame(self)
        bar_height = 50
        self.bottom_bar.setGeometry(
            self.main_frame.x(),
            self.main_frame.y() + self.main_frame.height() + 5,
            self.main_frame.width(),
            bar_height
        )
        self.bottom_bar.show()

        btn_w = 90
        btn_h = 32

        self.sort_btn = QPushButton(self.sort_label(), self.bottom_bar)
        self.sort_btn.setFont(fonts['small'])
        self.sort_btn.setStyleSheet(self.gray_style)
        self.sort_btn.setFixedSize(btn_w, btn_h)
        self.sort_btn.clicked.connect(lambda: self.toggle_sort())
        self.sort_btn.show()

        self.return_btn = QPushButton("返回", self.bottom_bar)
        self.return_btn.setFont(fonts['small'])
        self.return_btn.setStyleSheet(self.gray_style)
        self.return_btn.setFixedSize(btn_w, btn_h)
        self.return_btn.clicked.connect(lambda: self.back_to_main())
        self.return_btn.hide()  # 初始隐藏
        # self.return_btn.show()

        self.toggle_btn = QPushButton("简体" if self.is_trad else "繁體", self.bottom_bar)
        self.toggle_btn.setFont(fonts['small'])
        self.toggle_btn.setStyleSheet(self.gray_style)
        self.toggle_btn.setFixedSize(btn_w, btn_h)
        self.toggle_btn.clicked.connect(lambda: self.toggle_lang())
        self.toggle_btn.show()

        QTimer.singleShot(0, self._init_bottom_btn_pos)

        btn_w = 90
        btn_h = 32
        self.sort_btn.setFixedSize(btn_w, btn_h)
        self.return_btn.setFixedSize(btn_w, btn_h)
        self.toggle_btn.setFixedSize(btn_w, btn_h)

        # ===== 右上角复选框（在主框架外，绝对定位）=====
        self.long_only_cb = QCheckBox("只顯示龍譜" if self.is_trad else "只显示龙谱", self)
        self.long_only_cb.setFont(fonts['small'])
        self.long_only_cb.stateChanged.connect(lambda: self.update_list())
        self.long_only_cb.setStyleSheet("""
            QCheckBox {
                background-color: rgba(50, 50, 50, 150);
                color: white;
                padding: 5px 8px;
                border-radius: 3px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        self.long_only_cb.adjustSize()
        # 右上角，距离顶部10px，距离右边10px
        self.long_only_cb.move(self.width() - self.long_only_cb.width() - 10, 10)

        # 初始化变量
        self.detail_text = None
        self.long_raw = None
        self.qin_raw = None
        self.detail_frame = None
        self.detail_title = None
        self.qin_btn_detail = None  # 详情页的钦谱按钮
        self.long_btn_detail = None  # 详情页的龙谱按钮
        self.btn_frame = None
        self.qin_raw_s = None
        self.qin_raw_t = None
        self.long_raw_s = None
        self.long_raw_t = None
        self.detail_widget = None

        self.update_list()
        self.show()

    def _init_bottom_btn_pos(self):
        bar_w = self.bottom_bar.width()
        bar_h = self.bottom_bar.height()

        btn_w = self.sort_btn.width()
        btn_h = self.sort_btn.height()

        self.sort_btn.move(int(bar_w * 0.10 - btn_w / 2), int(bar_h / 2 - btn_h / 2))
        self.return_btn.move(int(bar_w * 0.50 - btn_w / 2), int(bar_h / 2 - btn_h / 2))
        self.toggle_btn.move(int(bar_w * 0.90 - btn_w / 2), int(bar_h / 2 - btn_h / 2))

    @log_exceptions
    def toggle_long_only(self):
        """切换只显示龙谱模式"""
        self.update_list()

    @staticmethod
    def show_ci_pu(text_area: QTextEdit, raw_text: str):
        """在指定 QTextEdit 控件中显示词谱内容"""
        if raw_text is None:
            return
        text_area.setReadOnly(False)
        text_area.clear()
        text_area.setPlainText(raw_text)
        text_area.setReadOnly(True)

    @log_exceptions
    def toggle_lang(self):
        """翻转简繁状态并全局刷新"""
        self.is_trad = not self.is_trad

        # 窗口标题
        self.setWindowTitle("詞譜查詢" if self.is_trad else "词谱查询")

        # 搜索提示
        self.search_hint.setText("輸入詞譜名/拼音：" if self.is_trad else "输入词谱名/拼音：")

        # 按钮文本
        self.toggle_btn.setText("简体" if self.is_trad else "繁體")
        self.sort_btn.setText(self.sort_label())
        self.long_only_cb.setText("只顯示龍譜" if self.is_trad else "只显示龙谱")
        self.return_btn.setText("返回")

        # 刷新详情页语言
        if getattr(self, 'detail_widget', None) is not None and not sip.isdeleted(self.detail_widget):
            self._refresh_detail_lang()

        self.update_list()

    def _refresh_detail_lang(self):
        """刷新详情页中的语言"""
        self.qin_raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.long_raw = self.long_raw_t if self.is_trad else self.long_raw_s

        # 标题
        self.detail_title.setText(
            self.current_item['names_trad'][0] if self.is_trad else self.current_item['names'][0]
        )

        # 按钮
        if hasattr(self, 'qin_btn_detail') and self.qin_btn_detail is not None:
            self.qin_btn_detail.setText('欽譜' if self.is_trad else '钦谱')
            self.qin_btn_detail.clicked.disconnect()
            self.qin_btn_detail.clicked.connect(lambda: self._on_qin())

        if hasattr(self, 'long_btn_detail') and self.long_btn_detail is not None:
            self.long_btn_detail.setText('龍譜' if self.is_trad else '龙谱')
            self.long_btn_detail.clicked.disconnect()
            self.long_btn_detail.clicked.connect(lambda: self._on_long())

        # 文本刷新
        raw = self.qin_raw if self.current_show == 'qin' else self.long_raw
        self.show_ci_pu(self.detail_text, raw)

    def sort_label(self):
        return ["排序:拼音", "排序:字數", "排序:類型"][self.sort_mode] if self.is_trad else \
            ["排序:拼音", "排序:字数", "排序:类型"][self.sort_mode]

    @log_exceptions
    def toggle_sort(self):
        self.sort_mode = (self.sort_mode + 1) % 3
        self.current_state['sort_mode'] = self.sort_mode
        self.sort_btn.setText(self.sort_label())
        self.update_list()

    @log_exceptions
    def update_list(self, _=None):
        key = self.search_var.text().strip().lower()
        self.result_box.clear()

        def sort_key(ci_pais):
            t = ci_pais['type']
            if self.sort_mode == 0:
                return ci_pais['full']
            elif self.sort_mode == 1:
                return t[1]
            else:
                order_map = {'平': 0, '仄': 1, '换': 2, '叶': 3}
                order_val = order_map[t[-1][0]]
                num = t[1]
                return order_val, num, ci_pais['full']

        ordered = sorted(self.indexed, key=sort_key)

        # 龙谱过滤逻辑
        if self.long_only_cb.isChecked():
            ordered = [item for item in ordered if item['idx'] in self.long_only_idx]

        matched = []
        if key:
            for item in ordered:
                if any(key in n for n in item['names']) or any(key in p for p in item['pinyins']):
                    matched.append(item)
        else:
            matched = ordered

        self.current_matched = matched

        if not matched:
            self.no_result_label.setText("找不到符合條件的詞譜" if self.is_trad else "找不到符合条件的词谱")
            self.no_result_label.show()
            return
        else:
            self.no_result_label.hide()
            self.no_result_label.setText("")

        displays = [it['display_t'] if self.is_trad else it['display_s'] for it in matched]

        self.result_box.addItems(displays)

    @log_exceptions
    def open_detail(self, _=None):
        selected_items = self.result_box.selectedIndexes()
        if not selected_items:
            return
        idx_in_matched = selected_items[0].row()
        item = self.current_matched[idx_in_matched]
        self.show_detail(item)

    @staticmethod
    def read_file(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def load_ci_files(self, item):
        idx = item['idx']
        return {
            'qin_raw_s': self.read_file(os.path.join(CI_ORIGIN, f'cipai_{idx}.txt')),
            'qin_raw_t': self.read_file(os.path.join(CI_TRAD, f'cipai_{idx}_trad.txt')),
            'long_raw_s': self.read_file(os.path.join(CI_LONG_ORIGIN, f'cipai_{idx}_long.txt')),
            'long_raw_t': self.read_file(os.path.join(CI_LONG_TRAD, f'cipai_{idx}_long_trad.txt')),
        }

    def _on_qin(self):
        self.current_show = 'qin'
        raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.show_ci_pu(self.detail_text, raw)

    def _on_long(self):
        self.current_show = 'long'
        raw = self.long_raw_t if self.is_trad else self.long_raw_s
        self.show_ci_pu(self.detail_text, raw)

    @log_exceptions
    def show_detail_body(self, detail_widget: QWidget, btn_layout: QHBoxLayout, files_dict: dict):
        """根据已读文件显示词谱内容，并创建钦谱/龙谱按钮"""
        # 按当前模式选取简/繁体
        self.qin_raw_s = files_dict['qin_raw_s']
        self.qin_raw_t = files_dict['qin_raw_t']
        self.long_raw_s = files_dict['long_raw_s']
        self.long_raw_t = files_dict['long_raw_t']
        self.qin_raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.long_raw = self.long_raw_t if self.is_trad else self.long_raw_s

        small_font = self.fonts['small']

        # 钦谱按钮
        self.qin_btn_detail = QPushButton('欽譜' if self.is_trad else '钦谱')
        self.qin_btn_detail.setFont(small_font)
        self.qin_btn_detail.setStyleSheet("""
            QPushButton {
                background-color: #c9a6eb;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
                min-width: 60px;
                max-width: 80px;
            }
            QPushButton:hover {
                background-color: #b893d8;
            }
        """)
        self.qin_btn_detail.clicked.connect(self._on_qin)
        btn_layout.addWidget(self.qin_btn_detail)

        # 龙谱按钮（有内容才显示）
        if self.long_raw is not None:
            self.long_btn_detail = QPushButton('龍譜' if self.is_trad else '龙谱')
            self.long_btn_detail.setFont(small_font)
            self.long_btn_detail.setStyleSheet("""
                QPushButton {
                    background-color: #c9a6eb;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 5px;
                    min-width: 60px;
                    max-width: 80px;
                }
                QPushButton:hover {
                    background-color: #b893d8;
                }
            """)
            self.long_btn_detail.clicked.connect(self._on_long)
            btn_layout.addWidget(self.long_btn_detail)

        # 注意：这里不再调用 show_ci_pu，由调用者负责
        self.detail_frame = detail_widget

    @log_exceptions
    def show_detail(self, item: dict):
        """显示词谱详情（修复版）"""
        # 根据"只显示龙谱"选项决定默认显示的内容
        self.current_show = 'long' if self.long_only_cb.isChecked() else 'qin'

        self.main_frame.hide()
        self.sort_btn.hide()  # 隐藏排序按钮
        self.long_only_cb.hide()  # 隐藏龙谱复选框
        self.return_btn.show()  # 显示返回按钮

        self.current_item = item

        geo = self.main_frame.geometry()
        self.detail_widget = QWidget(self)
        self.detail_widget.setGeometry(geo.x(), geo.y(), geo.width(), geo.height() - 60)

        layout = QVBoxLayout(self.detail_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # ===== 标题（居中，灰色背景）=====
        title_layout = QHBoxLayout()
        title_layout.addStretch()

        self.detail_title = QLabel(item['names_trad'][0] if self.is_trad else item['names'][0])
        self.detail_title.setFont(self.fonts['bigger'])
        self.detail_title.setStyleSheet("""
            background-color: rgba(50, 50, 50, 150);
            color: white;
            padding: 10px 30px;
            border-radius: 5px;
        """)
        self.detail_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_layout.addWidget(self.detail_title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # ===== 按钮区域（居中，紫色）=====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_frame = QWidget(self.detail_widget)
        btn_inner_layout = QHBoxLayout(self.btn_frame)
        btn_inner_layout.setSpacing(15)

        files_dict = self.load_ci_files(item)
        self.show_detail_body(self.detail_widget, btn_inner_layout, files_dict)

        btn_layout.addWidget(self.btn_frame)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # ===== 文本区域 =====
        self.detail_text = QTextEdit(self.detail_widget)
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(self.fonts['small'])
        self.detail_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.detail_text)

        # 现在显示正确的内容
        raw = self.qin_raw if self.current_show == 'qin' else self.long_raw
        self.show_ci_pu(self.detail_text, raw)

        self.detail_widget.show()

    @log_exceptions
    def back_to_main(self):
        # 删除详情页相关控件和属性
        if hasattr(self, 'detail_widget') and self.detail_widget is not None:
            # 修复：检查对象是否被删除
            try:
                if not sip.isdeleted(self.detail_widget):
                    if hasattr(self, 'qin_btn_detail') and self.qin_btn_detail is not None:
                        if not sip.isdeleted(self.qin_btn_detail):
                            self.qin_btn_detail.deleteLater()
                        self.qin_btn_detail = None
                    if hasattr(self, 'long_btn_detail') and self.long_btn_detail is not None:
                        if not sip.isdeleted(self.long_btn_detail):
                            self.long_btn_detail.deleteLater()
                        self.long_btn_detail = None

                    self.detail_widget.deleteLater()
            except RuntimeError:
                pass  # 对象已被删除，忽略
            finally:
                # 确保清理引用
                if hasattr(self, 'detail_widget'):
                    del self.detail_widget

        for attr in ('detail_text', 'qin_raw', 'long_raw'):
            if hasattr(self, attr):
                delattr(self, attr)

        self.sort_btn.show()  # 显示排序按钮
        self.long_only_cb.show()  # 显示龙谱复选框
        self.return_btn.hide()  # 隐藏返回按钮
        self.main_frame.show()
        self.update_list()

    @log_exceptions
    def on_window_close(self):
        """关闭窗口时清理单例引用"""
        if hasattr(CiPuBrowser, '_instance'):
            CiPuBrowser._instance = None
        if hasattr(self, '_main_window_ref'):
            main_window = self._main_window_ref
            if hasattr(main_window, '_cipu_window'):
                delattr(main_window, '_cipu_window')
        if self.isVisible():
            self.close()
