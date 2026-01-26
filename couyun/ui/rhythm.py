"""
凑韵诗词格律检测工具主体tk模块，支持简体/繁体切换，使用方法请参照README文件。
"""
import json
import re
import sys
from time import time

from PyQt6 import sip
from PyQt6.QtCore import Qt, QMimeData, QSharedMemory
from PyQt6.QtGui import QIcon, QPixmap, QFont, QFontDatabase
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, \
    QTextEdit, QMessageBox, QApplication, QSizePolicy, QLineEdit, QComboBox
from PyQt6.sip import isdeleted

from couyun import CI_INDEX, STATE_PATH, FONT_PATH, ICO_PATH, bg_pic
from couyun.ci.ci_rhythm import CiRhythm
from couyun.ci.ci_search import search_ci, ci_type_extraction
from couyun.common.common import show_all_rhythm
from couyun.common.text_proceed import process_text
from couyun.shi.shi_rhythm import ShiRhythm
from couyun.ui.bootstrap.app import bootstrap
from couyun.ui.ci_pu_browser import CiPuBrowser
from couyun.ui.core.logger_config import get_logger, log_exceptions

logger = get_logger(__name__)

@ log_exceptions
def load_font(font_path: str) -> str:
    """加载 TTF 字体并返回字体 family 名称"""
    font_id = QFontDatabase.addApplicationFont(font_path)
    if font_id == -1:
        raise RuntimeError(f"加载字体失败: {font_path}")
    families = QFontDatabase.applicationFontFamilies(font_id)
    if not families:
        raise RuntimeError(f"字体未返回 family 名称: {font_path}")
    return families[0]


@ log_exceptions
def save_state(state: dict) -> None:
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)


@ log_exceptions
def on_close(state, window=None):
    """关闭窗口时的行为，卸载字体。将新状态写入json文件。"""
    save_state(state)
    logger.info('程序退出\n')
    if window is not None:
        window.close()


class SingleCharInput(QTextEdit):
    """自定义单行文本输入框：阻止回车键 + 粘贴自动清理换行"""

    @log_exceptions
    def __init__(self, parent=None):
        super().__init__(parent)
        # PyQt6 修正：使用 LineWrapMode 枚举
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.setMaximumHeight(30)
        # 可选：禁用滚动条，看起来更像单行输入
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    @log_exceptions
    def keyPressEvent(self, event):
        # PyQt6 修正：使用 Qt.Key.Key_Return 而不是 Qt.Key_Return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return  # 阻止回车，不调用父类方法
        super().keyPressEvent(event)

    @log_exceptions
    def insertFromMimeData(self, source):
        """粘贴时自动删除换行符"""
        if source.hasText():
            text = source.text()
            # 删除所有换行符和回车符
            cleaned = text.replace('\n', '').replace('\r', '').strip()

            # 创建新的 MIME 数据对象
            new_mime = QMimeData()
            new_mime.setText(cleaned)
            super().insertFromMimeData(new_mime)
        else:
            super().insertFromMimeData(source)

# noinspection PyTypeChecker
class RhythmCheckerGUI(QWidget):
    @log_exceptions
    def __init__(self, current_state):
        super().__init__()

        self.edition = 'v.2.0.0'

        # 简繁体转换
        self.s2t = str.maketrans('简输没标处状误里宽与为开对这选组并汉业态绝检验错无调逻块词诗转结内该体译留创识经闭择韵应钦华据号换'
                                 '辑么后显龙询图载准长数榆传干谱来诶务题类将样单确区当间写鹜钮点请两脚个关别参统凑书备录',
                                 '簡輸沒標處狀誤裏寛與為開對這選組幷漢業態絶檢驗錯無調邏塊詞詩轉結內該體譯畱創識經閉擇韻應欽華據號換'
                                 '輯麽後顯龍詢圖載準長數楡傳幹譜來誒務題類將樣單确區當間寫鶩鈕點請兩腳個關別參統湊書備錄')
        self.t2s = str.maketrans('簡輸沒標處狀誤裏寛與為開對這選組幷漢業態絶檢驗錯無調邏塊詞詩轉結內該體譯畱創識經閉擇韻應欽華據號換'
                                 '輯麽後顯龍詢圖載準長數楡傳幹譜來誒務題類將樣單确區當間寫鶩鈕點請兩腳個關別參統湊書備錄',
                                 '简输没标处状误里宽与为开对这选组并汉业态绝检验错无调逻块词诗转结内该体译留创识经闭择韵应钦华据号换'
                                 '辑么后显龙询图载准长数榆传干谱来诶务题类将样单确区当间写鹜钮点请两脚个关别参统凑书备录')

        self.current_state = current_state
        self.is_trad = current_state['is_trad']
        self.current_yun_shu = current_state['yun_shu']
        self.current_ci_pu = current_state['ci_pu']

        self.widgets_to_translate = []
        self.yun_shu_boxes = []
        self.cipu_boxes = []

        # 映射
        self.yun_shu_map = {1: '平水韵', 2: '中华新韵', 3: '中华通韵'}
        self.ci_pu_map = {1: '钦定词谱', 2: '龙榆生词谱'}
        self.yunshu_reverse_map = {'词林正韵': 1, "平水韵": 1, "中华新韵": 2, "中华通韵": 3,
                                   '詞林正韻': 1, "平水韻": 1, "中華新韻": 2, "中華通韻": 3}
        self.ci_pu_reverse_map = {'钦定词谱': 1, "龙榆生词谱": 2, '欽定詞譜': 1, "龍楡生詞譜": 2}

        # 字体与样式
        font_family = load_font(FONT_PATH)
        self.small_font = QFont(font_family, 13)
        self.default_font = QFont(font_family, 14)
        self.bigger_font = QFont(font_family, 16)
        self.my_purple = "#c9a6eb"

        # ===== 主窗口配置 =====
        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        screen_width, screen_height = screen_size.width(), screen_size.height()

        # 窗口长度占屏幕高度的 60%
        win_width = int(screen_width * 0.65)
        win_height = int(win_width * 3 / 4)  # 4:3比例

        self.setFixedSize(win_width, win_height)
        self.setWindowTitle("湊韻" if self.is_trad else "凑韵")
        self.setWindowIcon(QIcon(ICO_PATH))

        # ===== 背景 =====
        self.bg_index = current_state.get('bg_index', 0)
        self.bg_label = QLabel(self)
        pixmap = QPixmap(bg_pic(self.bg_index))
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

        # ===== 主界面三个按钮 =====
        self.main_interface = QWidget(self)
        self.main_interface.setGeometry(0, 0, self.width(), self.height())

        main_layout = QVBoxLayout()
        # 移除整体居中对齐，改为通过stretch控制位置
        # main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 删除这行
        main_layout.setSpacing(40)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 可选：移除边距确保精确比例
        self.main_interface.setLayout(main_layout)

        main_layout.addStretch(40)

        # ===== 标题 =====
        title_label = QLabel('湊韻詩詞格律校驗工具' if self.is_trad else "凑韵诗词格律校验工具",
                             self.main_interface)
        title_label.setFont(self.bigger_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        title_label.setStyleSheet(
            "background-color: rgba(50, 50, 50, 150); color: white; padding: 10px; border-radius: 5px;"
        )
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.register(title_label)

        button_frame = QWidget(self.main_interface)
        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(30)
        button_frame.setLayout(button_layout)
        main_layout.addWidget(button_frame)

        self.poem_button = QPushButton("詩校驗" if self.is_trad else "诗校验", button_frame)
        self.poem_button.setFont(self.default_font)
        self.poem_button.setStyleSheet(f"background-color: {self.my_purple};")
        self.poem_button.setFixedWidth(200)
        self.poem_button.setFixedHeight(45)
        self.poem_button.clicked.connect(lambda: self.open_poem_interface())
        button_layout.addWidget(self.poem_button)
        self.register(self.poem_button)

        self.ci_button = QPushButton("詞校驗" if self.is_trad else "词校验", button_frame)
        self.ci_button.setFont(self.default_font)
        self.ci_button.setStyleSheet(f"background-color: {self.my_purple};")
        self.ci_button.setFixedWidth(200)
        self.ci_button.setFixedHeight(45)
        self.ci_button.clicked.connect(lambda: self.open_ci_interface())
        button_layout.addWidget(self.ci_button)
        self.register(self.ci_button)

        self.char_button = QPushButton("查字", button_frame)
        self.char_button.setFont(self.default_font)
        self.char_button.setStyleSheet(f"background-color: {self.my_purple};")
        self.char_button.setFixedWidth(200)
        self.char_button.setFixedHeight(45)
        self.char_button.clicked.connect(lambda: self.open_char_interface())
        button_layout.addWidget(self.char_button)
        self.register(self.char_button)

        main_layout.addStretch(60)

        # ===== 底部三个按钮 =====
        bottom_y = self.height() - 40
        self.cover_button = QPushButton('切換封面' if self.is_trad else "切换封面", self)
        self.cover_button.setFont(self.small_font)
        self.cover_button.clicked.connect(lambda: self.switch_background())
        self.cover_button.setGeometry(10, bottom_y, 90, 30)
        self.register(self.cover_button)

        self.toggle_button = QPushButton('简体' if self.is_trad else "繁體", self)
        self.toggle_button.setFont(self.small_font)
        self.toggle_button.clicked.connect(lambda: self.toggle_language())
        self.toggle_button.setGeometry(self.width() - 100, bottom_y, 90, 30)

        self.ci_pu_button = QPushButton('詞譜查詢' if self.is_trad else "词谱查询", self)
        self.ci_pu_button.setFont(self.small_font)
        self.ci_pu_button.clicked.connect(lambda: self.open_cipu_browser())
        self.ci_pu_button.setGeometry(int(self.width() * 0.46), bottom_y, 90, 30)
        self.register(self.ci_pu_button)

        self.version_label = QLabel(self.edition, self)
        self.version_label.setFont(self.small_font)
        self.version_label.setStyleSheet(
            "background-color: rgba(50, 50, 50, 150); color: white; padding: 5px 8px; border-radius: 3px;"
        )
        self.version_label.adjustSize()
        self.version_label.move(self.width() - self.version_label.width() - 10, 10)

        # ===== 保留原变量顺序 =====
        self.input_text = None
        self.output_text = None
        self.cipai_form = None
        self.scrollbar = None
        self.cipai_var = None
        self.yunshu_var = None
        self.cipu_var = None
        self.current_output_text = None
        self.current_input_text = None
        self.background_image = None
        self.current_generic_widget = None
        self._cipu_window = None
        self._memory_window = None

    @log_exceptions
    def cc_convert(self, text, to_trad: bool):
        """根据目标模式转换文本"""
        return text.translate(self.s2t) if to_trad else text.translate(self.t2s)

    @log_exceptions
    def open_cipu_browser(self):
        if hasattr(self, "_cipu_window"):
            try:
                if self._cipu_window is not None and self._cipu_window.isVisible():
                    self._cipu_window.raise_()
                    self._cipu_window.activateWindow()
                    return
            except RuntimeError:
                # Qt 对象已被销毁
                self._cipu_window = None

        # 创建新的子窗口
        self._cipu_window = CiPuBrowser(
            parent=None,
            json_path=CI_INDEX,
            fonts={
                'small': self.small_font,
                'default': self.default_font,
                'bigger': self.bigger_font
            },
            state=self.current_state
        )
        self._cipu_window.show()

    @log_exceptions
    def box_toggle(self, boxes, single_map, current, to_traditional: bool):
        """安全处理简繁切换下拉框"""
        for cb in boxes:
            try:
                if isdeleted(cb):
                    continue

                if to_traditional:
                    trad_map = {k: v.translate(self.s2t) for k, v in single_map.items()}
                    values = [trad_map[k] for k in sorted(trad_map)]
                    current_text = trad_map[current]
                else:
                    values = [single_map[k] for k in sorted(single_map)]
                    current_text = single_map[current]

                cb.clear()
                cb.addItems(values)
                cb.setCurrentText(current_text)

            except Exception as e:
                print(f"box_toggle 在对 {cb} 时出错: {e}")

    @log_exceptions
    def translate_new_widgets(self, start_widgets, start_yun, start_ci):
        """新界面创建后，若当前是繁体模式，立即翻译新增控件和下拉框"""
        if not self.is_trad:
            return

        for w in self.widgets_to_translate[start_widgets:]:
            try:
                orig_text = w.text()
                w.setText(orig_text.translate(self.s2t))
            except Exception as e:
                logger.warning(f"翻译控件失败 {w}: {e}")

        self.box_toggle(self.yun_shu_boxes[start_yun:], self.yun_shu_map, self.current_yun_shu, True)
        self.box_toggle(self.cipu_boxes[start_ci:], self.ci_pu_map, self.current_ci_pu, True)

    @staticmethod
    @log_exceptions
    def display_result(ot, res):
        """统一输出结果到 QTextEdit 控件"""
        ot.show()
        ot.setReadOnly(False)
        ot.clear()
        ot.insertPlainText(res)
        ot.setReadOnly(True)

    @log_exceptions
    def my_warn(self, title, msg):
        if self.is_trad:
            title = title.translate(self.s2t)
            msg = msg.translate(self.s2t)
        QMessageBox.warning(self, title, msg)

    @log_exceptions
    def register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    @log_exceptions
    def toggle_language(self):
        """在简体和繁体之间切换"""
        to_trad = not self.is_trad  # 目标模式

        # 先处理普通可翻译控件
        alive_widgets = []
        for widget in self.widgets_to_translate:
            if widget is None or sip.isdeleted(widget):  # 如果控件已经被删除，跳过
                continue
            try:
                orig_text = widget.text()
                widget.setText(self.cc_convert(orig_text, to_trad))
                alive_widgets.append(widget)
            except (AttributeError, RuntimeError):
                continue
        self.widgets_to_translate = alive_widgets

        # 更新下拉框（如果它们还存在）
        self.box_toggle(self.yun_shu_boxes, self.yun_shu_map, self.current_yun_shu, to_trad)
        self.box_toggle(self.cipu_boxes, self.ci_pu_map, self.current_ci_pu, to_trad)

        if hasattr(self, 'toggle_button') and self.toggle_button is not None:
            self.toggle_button.setText('繁體' if self.is_trad else '简体')

        self.setWindowTitle('凑韵' if not to_trad else '湊韻')

        self.is_trad = to_trad
        self.current_state['is_trad'] = self.is_trad

    @log_exceptions
    def switch_background(self):
        self.bg_index = (self.bg_index + 1) % 3
        self.current_state['bg_index'] = self.bg_index
        self.background_image = QPixmap(bg_pic(self.bg_index))
        self.bg_label.setPixmap(self.background_image)

    @log_exceptions
    def create_generic_interface(self, title_text, hint_text, button_text, command_func, mode):
        old_widgets = len(self.widgets_to_translate)
        old_yun = len(self.yun_shu_boxes)
        old_ci = len(self.cipu_boxes)

        self.main_interface.hide()
        if hasattr(self, 'bottom_button_frame'):
            self.bottom_button_frame.hide()

        generic = QWidget(self)
        generic.setGeometry(0, 0, self.width(), self.height())
        self.current_generic_widget = generic

        self.cover_button.raise_()
        self.toggle_button.raise_()
        self.ci_pu_button.raise_()

        # ===== 外层：整体上下左右居中 =====
        outer_layout = QVBoxLayout(generic)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        outer_layout.addStretch(1)

        center_row = QWidget()
        center_row_layout = QHBoxLayout(center_row)
        center_row_layout.setContentsMargins(0, 0, 0, 0)
        center_row_layout.addStretch(1)

        # ===== 内容面板 =====
        content_panel = QWidget()
        content_layout = QVBoxLayout(content_panel)
        content_layout.setSpacing(6)
        content_layout.setContentsMargins(10, 10, 10, 10)

        center_row_layout.addWidget(content_panel)
        center_row_layout.addStretch(1)

        outer_layout.addWidget(center_row)
        outer_layout.addStretch(1)

        # ===== 灰底文字样式 =====
        label_style = (
            "background-color: rgba(0,0,0,150);"
            "color: white;"
            "padding: 2px 6px;"
            "border-radius: 3px;"
        )

        def make_label(text, font):
            lb = QLabel(text)
            lb.setFont(font)
            lb.setStyleSheet(label_style)
            lb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self.register(lb)
            return lb

        def make_row(label_text, widget, fixed_w=None):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(6)

            lb = make_label(label_text, self.default_font)
            rl.addWidget(lb)

            widget.setFont(self.default_font)
            if fixed_w:
                widget.setFixedWidth(fixed_w)
            rl.addWidget(widget)
            rl.addStretch(1)
            return row

        # ===== 标题 =====
        title_label = make_label(title_text, self.bigger_font)
        content_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # ===== 韵书选择 =====
        if mode != 's':
            if mode == 'c':
                self.yun_shu_map[1] = '词林正韵'
            else:
                self.yun_shu_map[1] = '平水韵'

            self.yunshu_var = QComboBox()
            self.yunshu_var.addItems([self.yun_shu_map[k] for k in sorted(self.yun_shu_map)])
            self.yunshu_var.setCurrentText(self.yun_shu_map[self.current_yun_shu])
            self.yunshu_var.currentIndexChanged.connect(lambda: self.on_yunshu_change())
            self.yun_shu_boxes.append(self.yunshu_var)

            content_layout.addWidget(make_row("选择韵书:", self.yunshu_var, fixed_w=180))

        # ===== 词校验模块 =====
        if mode == 'c':
            self.cipai_var = QLineEdit()
            content_layout.addWidget(make_row("输入词牌:", self.cipai_var, fixed_w=200))

            self.cipai_form = QLineEdit()
            content_layout.addWidget(make_row("格式:", self.cipai_form, fixed_w=120))

            self.cipu_var = QComboBox()
            self.cipu_var.addItems([self.ci_pu_map[k] for k in sorted(self.ci_pu_map)])
            self.cipu_var.setCurrentText(self.ci_pu_map[self.current_ci_pu])
            self.cipu_var.currentIndexChanged.connect(lambda: self.on_cipu_change())
            self.cipu_boxes.append(self.cipu_var)

            content_layout.addWidget(make_row("选择词谱:", self.cipu_var, fixed_w=220))

        # ===== 提示 =====
        il = make_label(hint_text, self.default_font)
        content_layout.addWidget(il, alignment=Qt.AlignmentFlag.AlignLeft)

        # ===== 输入输出 =====
        it_w = int(self.width() * (0.33 if mode == 'c' else 0.32))
        ot_w = int(self.width() * (0.63 if mode == 'c' else 0.52))
        max_h = int(self.height() * 0.8)

        io_container = QWidget()
        io_layout = QVBoxLayout(io_container) if mode == 's' else QHBoxLayout(io_container)
        io_layout.setSpacing(8)
        io_layout.setContentsMargins(0, 0, 0, 0)

        if mode == 's':
            it = SingleCharInput()
        else:
            it = QTextEdit()
        it.setAcceptRichText(False)
        it.setFont(self.small_font)
        it.setFixedWidth(it_w)
        it.setFixedHeight(30 if mode == 's' else int(max_h * 0.55))

        ot = QTextEdit()
        ot.setAcceptRichText(False)
        ot.setFont(self.small_font)
        ot.setReadOnly(True)
        ot.setFixedWidth(ot_w)
        ot.setFixedHeight(int(max_h * 0.55))
        ot.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        ot.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        ot.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        ot.hide()

        io_layout.addStretch(1)
        io_layout.addWidget(it)
        io_layout.addWidget(ot)
        io_layout.addStretch(1)

        content_layout.addWidget(io_container)

        # ===== 按钮区 =====
        bf = QWidget()
        bf_layout = QHBoxLayout(bf)
        bf_layout.setSpacing(12)
        bf_layout.setContentsMargins(0, 0, 0, 0)

        def wrapped_command():
            try:
                if not ot.isVisible():
                    ot.show()
                command_func(it, ot)
            except Exception as e:
                print("wrapped_command error:", e)

        bf_layout.addStretch(1)

        btn = QPushButton(button_text)
        btn.setFont(self.default_font)
        btn.setStyleSheet(f"background-color: {self.my_purple}")
        btn.setFixedWidth(120)
        btn.clicked.connect(lambda: wrapped_command())
        bf_layout.addWidget(btn)
        self.register(btn)

        if mode == 'c':
            sam = QPushButton('载入例词')
            sam.setFont(self.default_font)
            sam.setStyleSheet(f"background-color: {self.my_purple}")
            sam.setFixedWidth(120)
            sam.clicked.connect(lambda: self.get_ci_sample())
            bf_layout.addWidget(sam)
            self.register(sam)

        back = QPushButton("返回")
        back.setFont(self.default_font)
        back.setStyleSheet(f"background-color: {self.my_purple}")
        back.setFixedWidth(120)
        back.clicked.connect(lambda: self.return_to_main())
        bf_layout.addWidget(back)
        self.register(back)

        bf_layout.addStretch(1)

        content_layout.addWidget(bf)
        self.translate_new_widgets(old_widgets, old_yun, old_ci)

        self.current_input_text = it
        self.current_output_text = ot

        generic.show()
        return it, ot

    @log_exceptions
    def get_ci_sample(self):
        ci_pai_name = self.cipai_var.text()  # QLineEdit 的内容用 .text()
        ci_form = self.cipai_form.text()  # QLineEdit 的内容用 .text()
        if not ci_pai_name:
            self.my_warn("找茬是吧？", "请输入词牌名！")
            return
        if not re.fullmatch(r'[0-9]+', ci_form):
            self.my_warn("找茬是吧？", "请输入半角阿拉伯数字！")
            return

        cp = ci_pai_name.strip()
        ci_num = search_ci(cp, self.current_ci_pu)
        if ci_num == 'err1':
            self.my_warn("找茬是吧？", "无法找到对应的词牌，请检查输入内容！")
            return
        if ci_num == 'err2':
            self.my_warn("要不检查下？", "这个词牌没有龙谱，请选择隔壁钦谱！")
            return

        all_types = ci_type_extraction(ci_num, self.current_ci_pu)
        all_length = len(all_types)
        if int(ci_form) > all_length or int(ci_form) < 1:  # 排除输入 0 的影响
            self.my_warn("找茬是吧？", "不存在此格式！")
            return

        if self.is_trad:
            sample_ci = all_types[int(ci_form) - 1]['origin_trad']
        else:
            sample_ci = all_types[int(ci_form) - 1]['origin']

        self.input_text.clear()
        self.input_text.insertPlainText(sample_ci)

    @log_exceptions
    def on_yunshu_change(self):
        text = self.yunshu_var.currentText()
        if not text:
            return  # 当前文本为空，直接忽略
        if text not in self.yunshu_reverse_map:
            logger.warning(f"当前韵书不存在 reverse_map: {text}")
            return
        self.current_yun_shu = self.yunshu_reverse_map[text]
        self.current_state['yun_shu'] = self.current_yun_shu

    @log_exceptions
    def on_cipu_change(self):
        text = self.cipu_var.currentText()
        if not text:
            return
        if text not in self.ci_pu_reverse_map:
            logger.warning(f"当前词谱不存在 reverse_map: {text}")
            return
        self.current_ci_pu = self.ci_pu_reverse_map[text]
        self.current_state['ci_pu'] = self.current_ci_pu

    @log_exceptions
    def open_poem_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="诗校验", hint_text='请输入需要分析的诗：',
            button_text="开始分析", command_func=self.check_poem, mode='p'
        )

    @log_exceptions
    def open_ci_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="词校验", hint_text='请输入需要校验的词：',
            button_text="开始分析", command_func=self.check_ci, mode='c'
        )

    @log_exceptions
    def open_char_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="查字", hint_text='请输入需要查询的汉字：',
            button_text="开始查询", command_func=self.check_char, mode='s'
        )

    @log_exceptions
    def return_to_main(self):
        # 只隐藏功能页，不动主界面结构
        if hasattr(self, 'current_generic_widget'):
            self.current_generic_widget.hide()
            self.current_generic_widget.deleteLater()
            self.current_generic_widget = None

        self.main_interface.show()

    @log_exceptions
    def check_poem(self, it, ot):
        text = it.toPlainText().strip()  # Tk: it.get("1.0", tk.END)
        start_time = time()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要校验的诗！")
            return

        processed, comma_pos = process_text(text)
        length = len(processed)
        if (length % 10 != 0 and length % 14 != 0) or length < 20:
            self.my_warn("要不检查下？", f"诗的字数不正确，可能有不能识别的生僻字，你输入了{length}字")
            it.setPlainText(processed)  # Tk: delete + insert
            return

        process = ShiRhythm(self.current_yun_shu, processed, comma_pos, self.is_trad)
        res = process.main_shi()
        msgs = {1: '一句的长短不符合律诗的标准！请检查标点及字数。',
                2: '你输入的每一个韵脚都不在韵书里面诶，我没法分析的！'}
        if res in msgs:
            self.my_warn("怎么回事？", msgs[res])
            return

        end_time = time()
        time_result = f'檢測完畢，耗時{end_time - start_time:.5f}s\n' if self.is_trad else f'检测完毕，耗时{end_time - start_time:.5f}s\n'
        res += time_result

        self.display_result(ot, res)  # 调用 display_result 输出

    @log_exceptions
    def check_ci(self, it, ot):
        text = it.toPlainText().strip()  # Tk: it.get("1.0", tk.END)
        start_time = time()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要校验的词！")
            return

        cp, fm = self.cipai_var.text().strip(), self.cipai_form.text().strip()  # QLineEdit.text()
        proc, proc_comma_pos = process_text(text)
        length = len(proc)

        process = CiRhythm(self.current_yun_shu, cp, proc, proc_comma_pos, fm,
                           self.current_ci_pu, self.is_trad)
        res = process.main_ci()

        msgs = {
            0: "不能找到你输入的词牌！",
            1: f"格式与输入词牌不匹配，可能有不能识别的生僻字，你输入了{length}字！",
            2: "格式数字错误！",
            3: f"输入的内容无法匹配已有的词牌，请检查内容或将词谱更换为钦谱，你输入了{length}字",
            4: "龙谱中没有该词谱，请切换为钦谱。"
        }
        if res in msgs:
            self.my_warn("要不检查下？", msgs[res])
            return

        end_time = time()
        time_result = f'檢測完畢，耗時{end_time - start_time:.5f}s\n\n' if self.is_trad else f'检测完毕，耗时{end_time - start_time:.5f}s\n\n'
        res += time_result

        self.display_result(ot, res)  # 输出结果

    @log_exceptions
    def check_char(self, it, ot):
        """
        查询第一个汉字的韵律信息
        注意：it 参数必须是 SingleCharInput 的实例（或保持原 QTextEdit 但已替换为 SingleCharInput）
        """
        # 直接获取文本，无需再处理回车符（SingleCharInput 已保证无换行）
        text = it.toPlainText().strip()

        # 空内容检查
        if not text:
            self.my_warn("找茬是吧？", "请输入需要查询的汉字！")
            return

        # 匹配第一个汉字（支持 CJK 扩展字符）
        match = re.search(r'[\u4e00-\u9fff\u3400-\u4dbf\u3007\u2642\U00020000-\U0002A6DF]', text)
        if not match:
            self.my_warn("你在干嘛呢？", "输入的内容中不含汉字！")
            return

        char = match.group(0)
        res = show_all_rhythm(char, self.is_trad)

        # 多字符警告
        if len(text) != 1:
            warn = '你輸入了多個字符，系統將查詢第一個漢字\n\n' if self.is_trad else '你输入了多个字符，系统将查询第一个汉字\n\n'
            res = warn + res

        self.display_result(ot, res)


APP_KEY = "RhythmChecker"

@ log_exceptions
def main():
    # 高 DPI 策略（跨平台，Qt 原生）
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    shared_mem = QSharedMemory(APP_KEY)
    if not shared_mem.create(1):
        sys.exit(0)
    current_state = bootstrap()
    main_window = RhythmCheckerGUI(current_state)
    main_window.show()
    app.aboutToQuit.connect(lambda: on_close(current_state, main_window))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
