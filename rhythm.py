"""
凑韵诗词格律检测工具主体tk模块，支持简体/繁体切换，使用方法请参照README文件。
目前问题：1.繁简切换问题 2.去扒繁体词谱
"""
import json
import re
import os
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox, font
import ctypes
from PIL import Image, ImageTk
from opencc import OpenCC

from common import show_all_rhythm, current_dir, current_state, state_file
from ci_search import search_ci, ci_type_extraction
from shi_rhythm import ShiRhythm
from ci_rhythm import CiRhythm
from ci_pu_browser import CiPuBrowser


def resource_path(*paths):
    """统一的资源路径拼接"""
    return os.path.join(current_dir, *paths)


def load_font(font_path):
    ctypes.windll.gdi32.AddFontResourceW(font_path, 0x10, 0)


def unload_font(font_path):
    ctypes.windll.gdi32.RemoveFontResourceW(font_path, 0x10, 0)


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


def convert_to_traditional(text, is_traditional, mode):
    """如果在繁体界面下转换，需要将除了诗歌以外的内容转换为繁体。"""
    if not is_traditional:
        return text
    cc = OpenCC('s2t')
    converted_lines = []
    if mode != 's':
        counter = 0
        meet_empty = False
        for line in text.split('\n'):
            # 空白行：计数归零，原样输出（也可转繁，按需求）
            if line.strip() == '':
                counter = 0
                converted_lines.append(line)
                meet_empty = True
                continue
            counter += 1
            if counter == 2:
                pos = line.rfind('\u3000')
                if pos == -1:  # 找不到 \u3000
                    converted_lines.append(cc.convert(line))
                else:
                    head = line[:pos + 1]  # 含 \u3000 本身
                    tail = line[pos + 1:]
                    converted_lines.append(head + cc.convert(tail).replace('鹹', '咸'))  # 轉換出錯修改
            elif not meet_empty:  # 其余计数（0、1、3、4…）
                converted_lines.append(cc.convert(line))
            else:
                converted_lines.append(cc.convert(line).replace('葉', '叶'))
    else:
        for line in text.split('\n'):
            if '：' in line:
                converted_line = line
            else:
                converted_line = cc.convert(line).replace('鹹', '咸')
            converted_lines.append(converted_line)
    converted_text = '\n'.join(converted_lines)
    return converted_text


def load_background_image(image_path):
    """加载并调整背景图片大小"""
    image = Image.open(image_path)
    image = image.resize(size_tuple, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def settings(mode):
    """根据模式调整窗口大小"""
    if mode in ['p', 'c']:
        return current_state['tk_value']['frame_width'][0]
    return current_state['tk_value']['frame_width'][1]


def save_state(state_path, state):
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)


def on_close(state):
    """关闭窗口时的行为，卸载字体。将新状态写入json文件。"""
    font_path = resource_path('font', "LXGWWenKaiMono-Regular.ttf")
    unload_font(font_path)
    save_state(state_file, state)
    root.destroy()


# noinspection PyTypeChecker
class RhythmCheckerGUI:
    def __init__(self, roots):
        self.edition = 'v.1.4.5'

        self.yunshu_var = None
        self.cipu_var = None
        self.opencc_s2t = OpenCC('s2t')
        self.opencc_t2s = OpenCC('t2s')
        self.is_traditional = current_state['is_traditional']

        # 翻译/下拉框分组
        self.widgets_to_translate = []
        self.yun_shu_boxes = []
        self.cipu_boxes = []

        # 映射
        self.yun_shu_map = {1: '平水韵', 2: '中华新韵', 3: '中华通韵'}
        self.ci_pu_map = {1: '钦定词谱', 2: '龙榆生词谱'}
        self.yunshu_reverse_map = {'词林正韵': 1, "平水韵": 1, "中华新韵": 2, "中华通韵": 3,
                                   '詞林正韻': 1, "平水韻": 1, "中華新韻": 2, "中華通韻": 3}
        self.ci_pu_reverse_map = {'钦定词谱': 1, "龙榆生词谱": 2, '欽定詞譜': 1, "龍榆生詞譜": 2}
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
        self.root.iconbitmap(ico_path)
        self.root.resizable(width=False, height=False)
        self.root.title("湊韻" if self.is_traditional else "凑韵")
        self.root.geometry(size_string)

        self.bg_images = ["ei.jpg", "ei_2.jpg", "ei_3.jpg"]
        self.bg_index = current_state['bg_index']
        self.background_image = load_background_image(os.path.join(jpg_fold, self.bg_images[self.bg_index]))
        self.background_label = tk.Label(self.root, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)

        self.cover_button = tk.Button(self.root, text='切換封面' if self.is_traditional else "切换封面",
                                      command=self.switch_background, font=self.small_font)
        self.cover_button.place(relx=0.01, rely=0.99, anchor='sw')
        self.toggle_button = tk.Button(self.root, text='简体' if self.is_traditional else "繁體",
                                       command=self.toggle_language, font=self.small_font)
        self.toggle_button.place(relx=0.99, rely=0.99, anchor='se')
        self.ci_pu_button = tk.Button(self.root, text='詞譜查詢' if self.is_traditional else "词谱查询",
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

    def cc_convert(self, text, to_traditional: bool):
        """根据目标模式转换文本"""
        return self.opencc_s2t.convert(text) if to_traditional else self.opencc_t2s.convert(text)

    def open_cipu_browser(self):
        # 防止连点
        if getattr(self, '_opening_cipu', False):
            return
        self._opening_cipu = True

        def _done():
            # 窗口关闭后把标志复位
            self._opening_cipu = False

        fonts = {'small': self.small_font,
                 'default': self.default_font,
                 'bigger': self.bigger_font}

        browser = CiPuBrowser(
            master=self.root,
            json_path=resource_path('ci_list', 'ci_index.json'),
            fonts=fonts,
            resource_path=resource_path,
            state=current_state,
            origin_dir=resource_path('ci_origin'),
            long_dir=resource_path('ci_long_origin'),
            origin_trad_dir=resource_path('ci_trad'),
            long_trad_dir=resource_path('ci_long_trad'),
        )
        # 窗口销毁时回调
        browser.protocol("WM_DELETE_WINDOW", lambda: (browser.destroy(), _done()))


    def box_toggle(self, boxes, single_map, current, to_traditional: bool):
        """统一处理简繁切换下拉框"""
        for cb in boxes:
            if to_traditional:
                trad_map = {k: self.opencc_s2t.convert(v) for k, v in single_map.items()}
                cb['values'] = [trad_map[k] for k in sorted(trad_map)]
                cb.set(trad_map[current])
            else:
                cb['values'] = [single_map[k] for k in sorted(single_map)]
                cb.set(single_map[current])

    def translate_new_widgets(self, start_widgets, start_yun, start_ci):
        """新界面创建后，若当前是繁体模式，立即翻译新增控件和下拉框"""
        # 只在当前已经是繁体时才做转换
        if not self.is_traditional:
            return
        for w in self.widgets_to_translate[start_widgets:]:
            w.config(text=self.opencc_s2t.convert(w.cget('text')))
        # 只把新增的下拉框翻译（传入起始索引）
        self.box_toggle(self.yun_shu_boxes[start_yun:], self.yun_shu_map, self.current_yun_shu, True)
        self.box_toggle(self.cipu_boxes[start_ci:], self.ci_pu_map, self.current_ci_pu, True)

    def display_result(self, ot, res, mode):
        """统一输出结果到 Text 控件"""
        res = convert_to_traditional(res, self.is_traditional, mode)
        if mode == 'p':
            ot.pack(side=tk.RIGHT, padx=5)
        elif mode == 'c':
            ot.pack(side=tk.RIGHT, padx=5)
        else:  # 's'
            ot.pack(side=tk.BOTTOM, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)

    # -----------------------------------------------

    def my_warn(self, title, msg):
        if self.is_traditional:
            title = self.opencc_s2t.convert(title)
            msg = self.opencc_s2t.convert(msg)
        messagebox.showwarning(title, msg)

    def register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    def toggle_language(self):
        """在简体和繁体之间切换（注意：使用目标模式来渲染）"""
        to_trad = not self.is_traditional  # 目标模式
        for widget in self.widgets_to_translate:
            orig = widget.cget('text')
            new = self.cc_convert(orig, to_trad)
            widget.config(text=new)

        # 统一处理两类下拉框（使用目标模式）
        self.box_toggle(self.yun_shu_boxes, self.yun_shu_map, self.current_yun_shu, to_trad)
        self.box_toggle(self.cipu_boxes, self.ci_pu_map, self.current_ci_pu, to_trad)

        # 按钮/标题文本（保留原来显示逻辑）
        btn_text = '繁體' if self.is_traditional else '简体'
        self.toggle_button.config(text=btn_text)
        change_text = '切换封面' if self.is_traditional else '切換封面'
        self.cover_button.config(text=change_text)
        cipu_text = '词谱查询' if self.is_traditional else '詞譜查詢'
        self.ci_pu_button.config(text=cipu_text)
        title_text = '凑韵' if self.is_traditional else '湊韻'
        self.root.title(title_text)

        # 最后更新状态标志
        self.is_traditional = to_trad
        current_state['is_traditional'] = self.is_traditional

    def switch_background(self):
        self.bg_index = (self.bg_index + 1) % len(self.bg_images)
        current_state['bg_index'] = self.bg_index
        image_path = resource_path("picture", self.bg_images[self.bg_index])
        self.background_image = load_background_image(image_path)
        self.background_label.config(image=self.background_image)

    def create_main_interface(self):
        self.main_interface = ttk.Frame(self.root)
        self.main_interface.pack(pady=current_state['tk_value']['main_pady'])

        label = '湊韻詩詞格律校驗工具' if self.is_traditional else "凑韵诗词格律校验工具"
        title_label = ttk.Label(self.main_interface, text=label, font=self.bigger_font)
        title_label.pack(pady=10)
        self.register(title_label)

        frame = ttk.Frame(self.main_interface)
        frame.pack(pady=10)

        poem_button = tk.Button(frame, text="詩校驗" if self.is_traditional else "诗校验",
                                command=self.open_poem_interface, font=self.default_font, bg=self.my_purple, width=20)
        poem_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(poem_button)

        ci_button = tk.Button(frame, text="詞校驗" if self.is_traditional else "词校验",
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
        pady_len = current_state['tk_value']['generic_pady']
        generic.pack(pady=pady_len[2] if mode == 's' else pady_len[1] if mode == 'c' else pady_len[0])

        title_label = ttk.Label(generic, text=title_text, font=self.bigger_font)
        title_label.pack(pady=10)
        self.register(title_label)

        if mode != 's':
            if mode == 'c':
                # 词模式下第1项为词林正韵
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
            ttk.Label(pf, text="选择词谱:", font=self.default_font).pack(side=tk.LEFT, padx=5)

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
            self.scrollbar = ttk.Scrollbar(mf, orient=tk.HORIZONTAL, command=ot.xview)
            ot.configure(xscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            # 初始高度设为0，不显示
            self.scrollbar.place(relx=0, rely=1, relwidth=1, height=0)
        elif mode == 'p':
            self.scrollbar = ttk.Scrollbar(mf, orient=tk.VERTICAL, command=ot.yview)
            ot.configure(yscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            # 初始高度设为0，不显示
            self.scrollbar.place(relx=0, rely=1, relwidth=1, height=0)

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

        # 若已是繁体模式，立即翻译新控件（只翻译新增部分）
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
        # 转换为简体再搜索
        cipai_to_s = OpenCC('t2s')
        cp = cipai_to_s.convert(ci_pai_name.strip())
        ci_num = search_ci(cp, self.current_ci_pu)
        if ci_num == 'err1':
            self.my_warn("找茬是吧？", "无法找到对应的词牌，请检查输入内容！")
            return
        if ci_num == 'err2':
            self.my_warn("要不检查下？", "这个词牌没有龙谱，请选择隔壁钦谱！")
        all_types = ci_type_extraction(ci_num, self.current_ci_pu)
        all_length = len(all_types)
        if int(ci_form) > all_length:
            self.my_warn("找茬是吧？", "不存在此格式！")
            return
        sample_ci_list = all_types[int(ci_form) - 1]['ci_sep']
        sample_ci = '。'.join(sample_ci_list).replace('\u3000', '，').replace('，，', '，') + '。'
        if self.is_traditional:
            sample_ci = self.opencc_s2t.convert(sample_ci)
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
        start_time = time.time()
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
        process = ShiRhythm(self.current_yun_shu, processed, processed_comma)
        res = process.main_shi()
        msgs = {1: '一句的长短不符合律诗的标准！请检查标点及字数。',
                2: '你输入的每一个韵脚都不在韵书里面诶，我没法分析的！'}
        if res in msgs:
            self.my_warn("怎么回事？", msgs[res])
            return
        end_time = time.time()
        time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n'
        res += time_result
        bar = current_state['tk_value']['shi_bar']
        self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
        self.display_result(ot, res, 'p')

    def check_ci(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        start_time = time.time()
        if not text:
            self.my_warn("找茬是吧？", "请输入需要校验的词！")
            return
        cipai_to_s = OpenCC('t2s')
        cp, fm = cipai_to_s.convert(self.cipai_var.get().strip()), self.cipai_form.get().strip()
        proc = extract_chinese(text)
        proc_with_comma = extract_chinese(text, comma_remain=True)
        length = len(proc)
        process = CiRhythm(self.current_yun_shu, cp, proc, proc_with_comma, fm, self.current_ci_pu)
        res = process.main_ci()
        msgs = {0: "不能找到你输入的词牌！", 1: f"格式与输入词牌不匹配，可能有不能识别的生僻字，你输入了{length}字！",
                2: "格式数字错误！", 3: f"输入的内容无法匹配已有的词牌，请检查内容或将词谱更换为钦谱，你输入了{length}字",
                4: "龙谱中没有该词谱，请切换为钦谱。"}
        if res in msgs:
            self.my_warn("要不检查下？", msgs[res])
            return
        end_time = time.time()
        time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n\n'
        res += time_result
        bar = current_state['tk_value']['ci_bar']
        self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
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
        res = show_all_rhythm(text)
        self.display_result(ot, res, 's')


ico_path = resource_path('picture', 'ei.ico')
jpg_fold = resource_path('picture')
size_tuple = current_state['tk_value']['size']
size_string = 'x'.join(map(str, size_tuple))
MUTEX_NAME = "RhythmChecker_v145"
ERROR_ALREADY_EXISTS = 183
kernel32 = ctypes.windll.kernel32
handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
last_error = kernel32.GetLastError()
if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (OSError, AttributeError, ctypes.ArgumentError):
        ctypes.windll.user32.SetProcessDPIAware()
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
    load_font(resource_path('font', "LXGWWenKaiMono-Regular.ttf"))
    root.tk.call('tk', 'scaling', 2)
    ttk.Style().theme_use('vista')
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(current_state))
    app = RhythmCheckerGUI(root)
    root.mainloop()
