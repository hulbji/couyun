"""
凑韵诗词格律检测工具主体tk模块，支持简体/繁体切换，使用方法请参照README文件。
"""
import ctypes
import os
import re
import sys
from time import time
import json
import tkinter as tk
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk

from couyun.ui.ci_pu_browser import CiPuBrowser
from couyun.ci.ci_rhythm import CiRhythm
from couyun.ci.ci_search import search_ci, ci_type_extraction
from couyun.common.common import show_all_rhythm
from couyun.shi.shi_rhythm import ShiRhythm
from couyun import (CI_INDEX, ASSETS_DIR, STATE_PATH, CI_ORIGIN, CI_LONG_ORIGIN,
                    CI_TRAD, CI_LONG_TRAD, FONT_PATH, ICO_PATH, bg_pic)


def scaled_tk_value():
    return {
        "size": [1200, 900],
        "main_pady": 200,
        "generic_pady": [180, 105, 165],
        "frame_width": [35, 65, 10, 5],
        "zi_width": [15, 45, 10, 5]
    }


def load_font(font_path) -> None:
    ctypes.windll.gdi32.AddFontResourceW(str(font_path))


def unload_font(font_path) -> None:
    ctypes.windll.gdi32.RemoveFontResourceW(str(font_path))


def load_state() -> dict:
    if os.path.isfile(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'is_traditional': False, 'yun_shu': 1, 'ci_pu': 1, 'bg_index': 0}

def save_state(state: dict) -> None:
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)


def extract_chinese(text: str, comma_remain=False) -> str:
    """删除输入文本中的非汉字部分以及括号内的部分"""
    text = re.sub(r'[(（].*?[)）]', '', text)
    hanzi_range = r'\u4e00-\u9fff\u3400-\u4dbf\u3007\u2642\U00020000-\U0002A6DF'
    if comma_remain:
        punctuation = r',\.\?!:，。？！、：'
        pattern = re.compile(f'[{hanzi_range}{punctuation}]')
    else:
        pattern = re.compile(f'[{hanzi_range}]')
    filtered_text = ''.join(pattern.findall(text)).replace('\n', '')
    return filtered_text


def load_background_image(image_path):
    """加载并调整背景图片大小"""
    image = Image.open(image_path)
    image = image.resize(size_tuple, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def settings(mode):
    """根据模式调整窗口大小"""
    if mode in ['p', 'c']:
        return tk_value['frame_width']
    return tk_value['zi_width']


def on_close(state):
    """关闭窗口时的行为，卸载字体。将新状态写入json文件。"""
    unload_font(FONT_PATH)
    save_state(state)
    root.destroy()


# noinspection PyTypeChecker
class RhythmCheckerGUI:
    def __init__(self, roots):
        self.edition = 'v.1.4.6'

        self.yunshu_var = None
        self.cipu_var = None
        self.s2t = str.maketrans('简输没标处状误里宽与为开对这选组并汉业态绝检验错无调逻块词诗转结内该体译留创识经闭择韵应钦华据号换'
                                 '辑么后显龙询图载准长数榆传干谱来诶务题类将样单确区当间写鹜钮点请两脚个关别参统凑书',
                                 '簡輸沒標處狀誤裏寛與為開對這選組幷漢業態絶檢驗錯無調邏塊詞詩轉結內該體譯畱創識經閉擇韻應欽華據號換'
                                 '輯麽後顯龍詢圖載準長數楡傳幹譜來誒務題類將樣單确區當間寫鶩鈕點請兩腳個關別參統湊書')
        self.t2s = str.maketrans('簡輸沒標處狀誤裏寛與為開對這選組幷漢業態絶檢驗錯無調邏塊詞詩轉結內該體譯畱創識經閉擇韻應欽華據號換'
                                 '輯麽後顯龍詢圖載準長數楡傳幹譜來誒務題類將樣單确區當間寫鶩鈕點請兩腳個關別參統湊書',
                                 '简输没标处状误里宽与为开对这选组并汉业态绝检验错无调逻块词诗转结内该体译留创识经闭择韵应钦华据号换'
                                 '辑么后显龙询图载准长数榆传干谱来诶务题类将样单确区当间写鹜钮点请两脚个关别参统凑书')
        self.is_trad = current_state['is_trad']

        # 翻译/下拉框分组
        self.widgets_to_translate = []
        self.yun_shu_boxes = []
        self.cipu_boxes = []

        # 映射
        self.yun_shu_map = {1: '平水韵', 2: '中华新韵', 3: '中华通韵'}
        self.ci_pu_map = {1: '钦定词谱', 2: '龙榆生词谱'}
        self.yunshu_reverse_map = {'词林正韵': 1, "平水韵": 1, "中华新韵": 2, "中华通韵": 3,
                                   '詞林正韻': 1, "平水韻": 1, "中華新韻": 2, "中華通韻": 3}
        self.ci_pu_reverse_map = {'钦定词谱': 1, "龙榆生词谱": 2, '欽定詞譜': 1, "龍楡生詞譜": 2}
        self.current_yun_shu = current_state['yun_shu']
        self.current_ci_pu = current_state['ci_pu']

        # 字体与样式
        self.small_font = font.Font(family="霞鹜文楷等宽", size=12)
        self.default_font = font.Font(family="霞鹜文楷等宽", size=14)
        self.bigger_font = font.Font(family="霞鹜文楷等宽", size=16)
        self.my_purple = "#c9a6eb"

        self.cipai_form = None
        self.scrollbar = None
        self.root = roots
        self.root.iconbitmap(ICO_PATH)
        self.root.resizable(width=False, height=False)
        self.root.title("湊韻" if self.is_trad else "凑韵")
        self.root.geometry(size_string)

        self.bg_images = ["ei.jpg", "ei_2.jpg", "ei_3.jpg"]
        self.bg_index = current_state['bg_index']
        self.background_image = load_background_image(bg_pic(self.bg_index))
        self.background_label = tk.Label(self.root, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)

        self.cover_button = tk.Button(self.root, text='切換封面' if self.is_trad else "切换封面",
                                      command=self.switch_background, font=self.small_font)
        self.cover_button.place(relx=0.01, rely=0.99, anchor='sw')
        self.toggle_button = tk.Button(self.root, text='简体' if self.is_trad else "繁體",
                                       command=self.toggle_language, font=self.small_font)
        self.toggle_button.place(relx=0.99, rely=0.99, anchor='se')
        self.ci_pu_button = tk.Button(self.root, text='詞譜查詢' if self.is_trad else "词谱查询",
                                      command=self.open_cipu_browser, font=self.small_font)
        self.ci_pu_button.place(relx=0.5, rely=0.99, anchor='s')
        self.version_label = tk.Label(self.root, text=self.edition, font=self.small_font)
        self.version_label.place(relx=0.99, rely=0.01, anchor='ne')

        self.input_text = None
        self.output_text = None
        self.main_interface = None
        self.cipai_var = None
        self._opening_cipu = False

        self.create_main_interface()

    def cc_convert(self, text, to_trad: bool):
        """根据目标模式转换文本"""
        return text.translate(self.s2t) if to_trad else text.translate(self.t2s)

    def open_cipu_browser(self):
        if getattr(self, '_opening_cipu', False):
            return
        self._opening_cipu = True

        def _done():
            self._opening_cipu = False

        fonts = {'small': self.small_font,
                 'default': self.default_font,
                 'bigger': self.bigger_font}

        browser = CiPuBrowser(
            master=self.root,
            json_path=CI_INDEX,
            fonts=fonts,
            resource_path = lambda *p: os.path.abspath(os.path.join(ASSETS_DIR, *p)),
            state=current_state,
            origin_dir=CI_ORIGIN,
            long_dir=CI_LONG_ORIGIN,
            origin_trad_dir=CI_TRAD,
            long_trad_dir=CI_LONG_TRAD,
            current_state=current_state
        )
        browser.protocol("WM_DELETE_WINDOW", lambda: (browser.destroy(), _done()))


    def box_toggle(self, boxes, single_map, current, to_traditional: bool):
        """统一处理简繁切换下拉框"""
        for cb in boxes:
            if to_traditional:
                trad_map = {k: v.translate(self.s2t) for k, v in single_map.items()}
                cb['values'] = [trad_map[k] for k in sorted(trad_map)]
                cb.set(trad_map[current])
            else:
                cb['values'] = [single_map[k] for k in sorted(single_map)]
                cb.set(single_map[current])

    def translate_new_widgets(self, start_widgets, start_yun, start_ci):
        """新界面创建后，若当前是繁体模式，立即翻译新增控件和下拉框"""
        # 只在当前已经是繁体时才做转换
        if not self.is_trad:
            return
        for w in self.widgets_to_translate[start_widgets:]:
            w.config(text=w.cget('text').translate(self.s2t))
        # 只把新增的下拉框翻译（传入起始索引）
        self.box_toggle(self.yun_shu_boxes[start_yun:], self.yun_shu_map, self.current_yun_shu, True)
        self.box_toggle(self.cipu_boxes[start_ci:], self.ci_pu_map, self.current_ci_pu, True)

    def display_result(self, ot, res, mode):
        """统一输出结果到 Text 控件"""
        # res = convert_to_traditional(res, self.is_traditional, mode)
        if mode == 'p':
            ot.pack(side=tk.RIGHT, padx=5)
            self.scrollbar.place(relx=1.005, rely=0.5, anchor='e', relheight=1.01, width=21)
        elif mode == 'c':
            ot.pack(side=tk.RIGHT, padx=5)
            self.scrollbar.place(relx=0.5, rely=1.01, anchor='s', relwidth=1.01, height=21)
        else:
            ot.pack(side=tk.BOTTOM, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)


    def my_warn(self, title, msg):
        if self.is_trad:
            title = title.translate(self.s2t)
            msg = msg.translate(self.s2t)
        messagebox.showwarning(title, msg)

    def register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    def toggle_language(self):
        """在简体和繁体之间切换（注意：使用目标模式来渲染）"""
        to_trad = not self.is_trad  # 目标模式
        for widget in self.widgets_to_translate:
            orig = widget.cget('text')
            new = self.cc_convert(orig, to_trad)
            widget.config(text=new)

        # 统一处理两类下拉框（使用目标模式）
        self.box_toggle(self.yun_shu_boxes, self.yun_shu_map, self.current_yun_shu, to_trad)
        self.box_toggle(self.cipu_boxes, self.ci_pu_map, self.current_ci_pu, to_trad)

        # 按钮/标题文本（保留原来显示逻辑）
        btn_text = '繁體' if self.is_trad else '简体'
        self.toggle_button.config(text=btn_text)
        change_text = '切换封面' if self.is_trad else '切換封面'
        self.cover_button.config(text=change_text)
        cipu_text = '词谱查询' if self.is_trad else '詞譜查詢'
        self.ci_pu_button.config(text=cipu_text)
        title_text = '凑韵' if self.is_trad else '湊韻'
        self.root.title(title_text)

        # 最后更新状态标志
        self.is_trad = to_trad
        current_state['is_trad'] = self.is_trad
        print(current_state)

    def switch_background(self):
        self.bg_index = (self.bg_index + 1) % 3
        current_state['bg_index'] = self.bg_index
        self.background_image = load_background_image(bg_pic(self.bg_index))
        self.background_label.config(image=self.background_image)

    def create_main_interface(self):
        self.main_interface = ttk.Frame(self.root)
        self.main_interface.pack(pady=tk_value['main_pady'])

        label = '湊韻詩詞格律校驗工具' if self.is_trad else "凑韵诗词格律校验工具"
        title_label = ttk.Label(self.main_interface, text=label, font=self.bigger_font)
        title_label.pack(pady=10)
        self.register(title_label)

        frame = ttk.Frame(self.main_interface)
        frame.pack(pady=10)

        poem_button = tk.Button(frame, text="詩校驗" if self.is_trad else "诗校验",
                                command=self.open_poem_interface, font=self.default_font, bg=self.my_purple, width=20)
        poem_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(poem_button)

        ci_button = tk.Button(frame, text="詞校驗" if self.is_trad else "词校验",
                              command=self.open_ci_interface, font=self.default_font, bg=self.my_purple, width=20)
        ci_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(ci_button)

        char_button = tk.Button(frame, text="查字", command=self.open_char_interface,
                                font=self.default_font, bg=self.my_purple, width=20)
        char_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(char_button)

    def create_generic_interface(self, title_text, hint_text, button_text, command_func, mode):
        old_widgets = len(self.widgets_to_translate)
        old_yun = len(self.yun_shu_boxes)
        old_ci = len(self.cipu_boxes)

        self.main_interface.pack_forget()
        generic = ttk.Frame(self.root)
        pady_len = tk_value['generic_pady']
        generic.pack(pady=pady_len[2] if mode == 's' else pady_len[1] if mode == 'c' else pady_len[0])

        title_label = ttk.Label(generic, text=title_text, font=self.bigger_font)
        title_label.pack(pady=10)
        self.register(title_label)

        if mode != 's':
            if mode == 'c':
                self.yun_shu_map[1] = '词林正韵'
            else:
                self.yun_shu_map[1] = '平水韵'

            fb = ttk.Frame(generic)
            fb.pack(pady=5, anchor=tk.W)
            fl = ttk.Label(fb, text="选择韵书:", font=self.default_font)
            fl.pack(side=tk.LEFT, padx=5)
            self.register(fl)
            self.yunshu_var = tk.StringVar()
            self.yunshu_var.set(self.yun_shu_map[self.current_yun_shu])
            cb = ttk.Combobox(fb, textvariable=self.yunshu_var,
                              font=self.default_font, width=15, state="readonly")
            cb['values'] = [self.yun_shu_map[k] for k in sorted(self.yun_shu_map)]
            cb.pack(side=tk.LEFT, padx=5)
            self.yun_shu_boxes.append(cb)
            self.yunshu_var.trace("w", lambda *args: self.on_yunshu_change())

        if mode == 'c':
            cf = ttk.Frame(generic)
            cf.pack(pady=5, anchor=tk.W)
            cl = ttk.Label(cf, text="输入词牌:", font=self.default_font)
            cl.pack(side=tk.LEFT, padx=5)
            self.register(cl)
            self.cipai_var = tk.StringVar()
            ttk.Entry(cf, textvariable=self.cipai_var,
                      font=self.default_font, width=15).pack(side=tk.LEFT, padx=5)

            ff = ttk.Frame(generic)
            ff.pack(pady=5, anchor=tk.W)
            fl2 = ttk.Label(ff, text="格式:", font=self.default_font)
            fl2.pack(side=tk.LEFT, padx=5)
            self.register(fl2)
            self.cipai_form = tk.StringVar()
            ttk.Entry(ff, textvariable=self.cipai_form,
                      font=self.default_font, width=10).pack(side=tk.LEFT, padx=5)

            pf = ttk.Frame(generic)
            pf.pack(pady=5, anchor=tk.W)
            fl3 = ttk.Label(pf, text="选择词谱:", font=self.default_font)
            fl3.pack(side=tk.LEFT, padx=5)
            self.register(fl3)
            self.cipu_var = tk.StringVar(value=self.ci_pu_map[self.current_ci_pu])
            cb_cipu = ttk.Combobox(pf, textvariable=self.cipu_var,
                                   values=[self.ci_pu_map[k] for k in sorted(self.ci_pu_map)],
                                   font=self.default_font, width=12, state="readonly")
            cb_cipu.pack(side=tk.LEFT, padx=5)
            self.cipu_boxes.append(cb_cipu)
            self.cipu_var.trace("w", lambda *args: self.on_cipu_change())

        mf = ttk.Frame(generic)
        mf.pack(pady=10)
        il = ttk.Label(mf, text=hint_text, font=self.default_font)
        il.pack(side=tk.TOP, pady=10, anchor=tk.W)
        self.register(il)

        it = tk.Text(mf, width=settings(mode)[0], height=1 if mode == 's' else 10,
                     font=self.small_font)
        it.pack(side=tk.TOP if mode == 's' else tk.LEFT, padx=5)

        ot = tk.Text(mf, width=settings(mode)[1], height=10,
                     font=self.small_font, wrap=tk.NONE, state=tk.DISABLED)
        ot.pack(side=tk.TOP if mode == 's' else tk.LEFT, padx=5)
        if mode == 'c':
            self.scrollbar = ttk.Scrollbar(ot, orient=tk.HORIZONTAL, command=ot.xview)
            ot.configure(xscrollcommand=self.scrollbar.set)
            self.scrollbar.place(relx=0.5, rely=1, anchor='s', relwidth=1, height=8)
            self.scrollbar.place_forget()
        elif mode == 'p':
            self.scrollbar = ttk.Scrollbar(ot, orient=tk.VERTICAL, command=ot.yview)
            ot.configure(yscrollcommand=self.scrollbar.set)
            self.scrollbar.place(relx=1, rely=0.5, anchor='e', relheight=1, width=8)
            self.scrollbar.place_forget()

        bf = ttk.Frame(generic)
        bf.pack(pady=10)
        btn = tk.Button(bf, text=button_text,
                        command=lambda: command_func(it, ot),
                        font=self.default_font, bg=self.my_purple,
                        width=settings(mode)[2])
        btn.pack(side=tk.LEFT, padx=5)
        self.register(btn)
        if mode == 'c':
            sam = tk.Button(bf, text='载入例词',
                            command=self.get_ci_sample,
                            font=self.default_font, bg=self.my_purple,
                            width=settings(mode)[2])
            sam.pack(side=tk.LEFT, padx=5)
            self.register(sam)
        back = tk.Button(bf, text="返回", command=self.return_to_main,
                         font=self.default_font, bg=self.my_purple,
                         width=settings(mode)[3])
        back.pack(side=tk.RIGHT, padx=5)
        self.register(back)
        ot.pack_forget()
        self.translate_new_widgets(old_widgets, old_yun, old_ci)

        return it, ot

    def get_ci_sample(self):
        ci_pai_name = self.cipai_var.get()
        ci_form = self.cipai_form.get()
        if not ci_pai_name:
            self.my_warn("找茬是吧？", "请输入词牌名！")
            return
        if not ci_form.isnumeric():
            self.my_warn("找茬是吧？", "请输入正确的格式！")
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
        if int(ci_form) > all_length:
            self.my_warn("找茬是吧？", "不存在此格式！")
            return
        if self.is_trad:
            sample_ci = all_types[int(ci_form) - 1]['origin_trad']
        else:
            sample_ci = all_types[int(ci_form) - 1]['origin']
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, sample_ci)

    def on_yunshu_change(self):
        self.current_yun_shu = self.yunshu_reverse_map[self.yunshu_var.get()]
        current_state['yun_shu'] = self.current_yun_shu

    def on_cipu_change(self):
        self.current_ci_pu = self.ci_pu_reverse_map[self.cipu_var.get()]
        current_state['ci_pu'] = self.current_ci_pu

    def open_poem_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="诗校验", hint_text='请输入需要分析的律诗或绝句：',
            button_text="开始分析", command_func=self.check_poem, mode='p'
        )

    def open_ci_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="词校验", hint_text='请输入需要校验的词：',
            button_text="开始分析", command_func=self.check_ci, mode='c'
        )

    def open_char_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="查字", hint_text='请输入需要查询的汉字：',
            button_text="开始查询", command_func=self.check_char, mode='s'
        )

    def return_to_main(self):
        for w in self.root.winfo_children():
            # 忽略所有 Toplevel 子窗口
            if isinstance(w, tk.Toplevel):
                continue
            if w not in (self.main_interface, self.toggle_button):
                w.pack_forget()
        self.main_interface.pack(pady=200)

    def check_poem(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        start_time = time()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要校验的诗！")
            return
        processed = extract_chinese(text)
        processed_comma = extract_chinese(text, comma_remain=True)
        length = len(processed)
        if (length % 10 != 0 and length % 14 != 0) or length < 20:
            self.my_warn("要不检查下？", f"诗的字数不正确，可能有不能识别的生僻字，你输入了{length}字")
            it.delete("1.0", tk.END)
            it.insert(tk.END, processed)
            return
        process = ShiRhythm(self.current_yun_shu, processed, processed_comma, self.is_trad)
        res = process.main_shi()
        msgs = {1: '一句的长短不符合律诗的标准！请检查标点及字数。',
                2: '你输入的每一个韵脚都不在韵书里面诶，我没法分析的！'}
        if res in msgs:
            self.my_warn("怎么回事？", msgs[res])
            return
        end_time = time()
        if self.is_trad:
            time_result = f'檢測完畢，耗時{end_time - start_time:.5f}s\n'
        else:
            time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n'
        res += time_result
        # bar = current_state['tk_value']['shi_bar']
        # self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
        self.display_result(ot, res, 'p')

    def check_ci(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        start_time = time()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要校验的词！")
            return
        cp, fm = self.cipai_var.get().strip(), self.cipai_form.get().strip()
        proc = extract_chinese(text)
        proc_with_comma = extract_chinese(text, comma_remain=True)
        length = len(proc)
        process = CiRhythm(self.current_yun_shu, cp, proc, proc_with_comma, fm,
                           self.current_ci_pu, self.is_trad)
        res = process.main_ci()
        msgs = {0: "不能找到你输入的词牌！", 1: f"格式与输入词牌不匹配，可能有不能识别的生僻字，你输入了{length}字！",
                2: "格式数字错误！", 3: f"输入的内容无法匹配已有的词牌，请检查内容或将词谱更换为钦谱，你输入了{length}字",
                4: "龙谱中没有该词谱，请切换为钦谱。"}
        if res in msgs:
            self.my_warn("要不检查下？", msgs[res])
            return
        end_time = time()
        if self.is_trad:
            time_result = f'檢測完畢，耗時{end_time - start_time:.5f}s\n\n'
        else:
            time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n\n'
        res += time_result
        # bar = current_state['tk_value']['ci_bar']
        # self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
        self.display_result(ot, res, 'c')

    def check_char(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要查询的汉字！")
            return
        if len(text) != 1:
            self.my_warn("找茬是吧？", "请输入单个汉字！")
            return
        if not re.match(r'[\u4e00-\u9fff\u3400-\u4dbf\u3007\u2642\U00020000-\U0002A6DF]', text):
            self.my_warn("你在干嘛呢？", "非汉字或超出区段（基本区及拓展A、B区）")
            return
        res = show_all_rhythm(text, self.is_trad)
        self.display_result(ot, res, 's')

if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (OSError, AttributeError, ctypes.ArgumentError):
        ctypes.windll.user32.SetProcessDPIAware()

current_state = load_state()
MUTEX_NAME = "RhythmChecker"
ERROR_ALREADY_EXISTS = 183
kernel32 = ctypes.windll.kernel32
handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
last_error = kernel32.GetLastError()
if last_error == ERROR_ALREADY_EXISTS:
    try:
        window_title = "湊韻" if current_state.get('is_traditional', False) else "凑韵"
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 5)   # SW_SHOW
            ctypes.windll.user32.SetForegroundWindow(hwnd)
    except (OSError, ctypes.WinError):
        pass
    sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    tk_value = scaled_tk_value()
    size_tuple = tk_value['size']
    size_string = 'x'.join(map(str, size_tuple))
    load_font(FONT_PATH)
    root.tk.call('tk', 'scaling', 2)
    ttk.Style().theme_use('vista')
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(current_state))
    app = RhythmCheckerGUI(root)
    root.mainloop()
