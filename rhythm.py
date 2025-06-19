"""凑韵诗词格律检测工具主体tk模块，支持简体/繁体切换，使用方法请参照README文件。"""

import re
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox, font
import ctypes
from PIL import Image, ImageTk
from opencc import OpenCC
import json

from common import show_all_rhythm, current_dir
from shi_rhythm import real_shi
from ci_rhythm import real_ci, search_ci, ci_type_extraction


def load_font(font_path):
    ctypes.windll.gdi32.AddFontResourceW(font_path, 0x10, 0)


def unload_font(font_path):
    ctypes.windll.gdi32.RemoveFontResourceW(font_path, 0x10, 0)


def load_state(state_path):
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_state(state_path, state):
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=4)


ico_path = os.path.join(current_dir, 'picture', 'ei.ico')
jpg_fold = os.path.join(current_dir, 'picture')
state_file = os.path.join(current_dir, 'state', 'state.json')
current_state = load_state(state_file)
size_tuple = current_state['tk_value']['size']
size_string = 'x'.join(map(str, size_tuple))
if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (OSError, AttributeError, ctypes.ArgumentError):
        ctypes.windll.user32.SetProcessDPIAware()


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
    for line in text.split('\n'):
        if "你的格式" in line:
            converted_line = cc.convert(line)
        elif '\t' in line or ' ' in line:
            sep = '\t' if '\t' in line else ' '
            word_part, non_word_part = line.split(sep, 1)
            converted_non_word = cc.convert(non_word_part)
            converted_line = f"{word_part}{sep}{converted_non_word}"
        elif '在：' in line and mode == 's':
            converted_line = line
        else:
            converted_line = cc.convert(line)
        converted_lines.append(converted_line)
    converted_text = '\n'.join(converted_lines)
    return converted_text.replace('鹹韻', "咸韻").replace('十五鹹', "十五咸")


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


def on_close(state):
    """关闭窗口时的行为，卸载字体。将新状态写入json文件。"""
    font_path = os.path.join(current_dir, 'font', "LXGWWenKaiMono-Regular.ttf")
    unload_font(font_path)
    save_state(state_file, state)
    root.destroy()


# noinspection PyTypeChecker,DuplicatedCode
class RhythmCheckerGUI:
    def __init__(self, roots):
        self.yunshu_var = None
        self.opencc_s2t = OpenCC('s2t')
        self.opencc_t2s = OpenCC('t2s')
        self.is_traditional = current_state['is_traditional']
        self.widgets_to_translate = []
        self.comboboxes = []

        self.yun_shu_map = {1: '平水韵', 2: '中华新韵', 3: '中华通韵'}
        self.current_yun_shu = current_state['yun_shu']

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

        self.input_text = None
        self.output_text = None
        self.main_interface = None
        self.cipai_var = None
        self.yunshu_reverse_map = {'词林正韵': 1, "平水韵": 1, "中华新韵": 2, "中华通韵": 3,
                                   '詞林正韻': 1, "平水韻": 1, "中華新韻": 2, "中華通韻": 3}

        self.create_main_interface()

    def register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    def toggle_language(self):
        """在简体和繁体之间切换"""
        for widget in self.widgets_to_translate:
            orig = widget.cget('text')
            new = self.opencc_t2s.convert(orig) if self.is_traditional else self.opencc_s2t.convert(orig)
            widget.config(text=new)
        for cb in self.comboboxes:
            if not self.is_traditional:
                trad_map = {k: self.opencc_s2t.convert(v) for k, v in self.yun_shu_map.items()}
                cb['values'] = [trad_map[k] for k in sorted(trad_map)]
                cb.set(trad_map[self.current_yun_shu])
            else:
                cb['values'] = [self.yun_shu_map[k] for k in sorted(self.yun_shu_map)]
                cb.set(self.yun_shu_map[self.current_yun_shu])
        btn_text = '繁體' if self.is_traditional else '简体'
        self.toggle_button.config(text=btn_text)
        change_text = '切换封面' if self.is_traditional else '切換封面'
        self.cover_button.config(text=change_text)
        title_text = '凑韵' if self.is_traditional else '湊韻'
        self.root.title(title_text)
        self.is_traditional = not self.is_traditional
        current_state['is_traditional'] = self.is_traditional

    def switch_background(self):
        self.bg_index = (self.bg_index + 1) % len(self.bg_images)
        current_state['bg_index'] = self.bg_index
        image_path = os.path.join(current_dir, "picture", self.bg_images[self.bg_index])
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
        old_comboboxes = len(self.comboboxes)

        self.main_interface.pack_forget()
        generic = ttk.Frame(self.root)
        pady_len = current_state['tk_value']['generic_pady']
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
            self.comboboxes.append(cb)
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
            self.scrollbar.place(relx=0, rely=1, relwidth=1, height=0)
        elif mode == 'p':
            self.scrollbar = ttk.Scrollbar(mf, orient=tk.VERTICAL, command=ot.yview)
            ot.configure(yscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
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

        # 若已是繁体模式，立即翻译新控件
        if self.is_traditional:
            for w in self.widgets_to_translate[old_widgets:]:
                w.config(text=self.opencc_s2t.convert(w.cget('text')))
            for cb_new in self.comboboxes[old_comboboxes:]:
                trad_map = {k: self.opencc_s2t.convert(v) for k, v in self.yun_shu_map.items()}
                cb_new['values'] = [trad_map[k] for k in sorted(trad_map)]
                cb_new.set(trad_map[self.current_yun_shu])

        return it, ot

    def get_ci_sample(self):
        ci_pai_name = self.cipai_var.get()
        ci_form = self.cipai_form.get()
        if not ci_pai_name:
            messagebox.showwarning("找茬是吧？", "请输入词牌名！")
            return
        if not ci_form.isnumeric():
            messagebox.showwarning("找茬是吧？", "请输入正确的格式！")
            return
        ci_num = search_ci(ci_pai_name)
        if ci_num is None:
            messagebox.showwarning("找茬是吧？", "无法找到对应的词牌，请检查输入内容！")
            return
        all_types = ci_type_extraction(ci_num)
        all_length = len(all_types)
        if int(ci_form) > all_length:
            messagebox.showwarning("找茬是吧？", "不存在此格式！")
            return
        sample_ci_list = all_types[int(ci_form) - 1]['ci_sep']
        sample_ci = '。'.join(sample_ci_list).replace('\u3000', '，').replace('，，', '，') + '。'
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, sample_ci)

    def on_yunshu_change(self):
        self.current_yun_shu = self.yunshu_reverse_map[self.yunshu_var.get()]
        current_state['yun_shu'] = self.current_yun_shu

    def open_poem_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="诗校验", hint_text='请输入需要分析的律诗或绝句：',
            button_text="开始分析", command_func=self.check_poem, mode='p'
        )

    def open_ci_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="词校验", hint_text='请输入需要分析的词：',
            button_text="开始分析", command_func=self.check_ci, mode='c'
        )

    def open_char_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="查字", hint_text='请输入需要查询的汉字：',
            button_text="开始查询", command_func=self.check_char, mode='s'
        )

    def return_to_main(self):
        for w in self.root.winfo_children():
            if w not in (self.main_interface, self.toggle_button):
                w.pack_forget()
        self.main_interface.pack(pady=200)

    def check_poem(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        start_time = time.time()
        if not text:
            title, msg = "找茬是吧？", "请输入需要校验的诗！"
            if self.is_traditional:
                title = self.opencc_s2t.convert(title)
                msg = self.opencc_s2t.convert(msg)
            messagebox.showwarning(title, msg)
            return
        processed = extract_chinese(text)
        processed_comma = extract_chinese(text, comma_remain=True)
        length = len(processed)
        if (length % 10 != 0 and length % 14 != 0) or length < 20:
            messagebox.showwarning("要不检查下？", f"诗的字数不正确，可能有不能识别的生僻字，你输入了{length}字")
            it.delete("1.0", tk.END)
            it.insert(tk.END, processed)
            return
        res = real_shi(self.current_yun_shu, processed, processed_comma)
        msgs = {1: '一句的长短不符合律诗的标准！请检查标点及字数。', 2: '你输入的每一个韵脚都不在韵书里面诶，我没法分析的！'}
        if res in msgs:
            title, msg = "怎么回事？", msgs[res]
            if self.is_traditional:
                title = self.opencc_s2t.convert(title)
                msg = self.opencc_s2t.convert(msg)
            messagebox.showwarning(title, msg)
            return
        end_time = time.time()
        time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n'
        res += time_result
        res = convert_to_traditional(res, self.is_traditional, 'p')
        bar = current_state['tk_value']['shi_bar']
        self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
        ot.pack(side=tk.RIGHT, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)

    def check_ci(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        start_time = time.time()
        if not text:
            messagebox.showwarning("找茬是吧？", "请输入需要校验的词！")
            return
        cipai_to_s = OpenCC('t2s')
        cp, fm = cipai_to_s.convert(self.cipai_var.get().strip()), self.cipai_form.get().strip()
        proc = extract_chinese(text)
        proc_with_comma = extract_chinese(text, comma_remain=True)
        length = len(proc)
        res = real_ci(self.current_yun_shu, cp, proc, proc_with_comma, fm)
        msgs = {0: "不能找到你输入的词牌！", 1: f"格式与输入词牌不匹配，可能有不能识别的生僻字，你输入了{length}字！",
                2: "格式数字错误！", 3: f"输入的内容无法匹配已有的词牌，请检查内容，你输入了{length}字"}
        if res in msgs:
            messagebox.showwarning("要不检查下？", msgs[res])
            return
        end_time = time.time()
        time_result = f'检测完毕，耗时{end_time - start_time:.5f}s\n'
        res += time_result
        res = convert_to_traditional(res, self.is_traditional, 'c')
        bar = current_state['tk_value']['ci_bar']
        self.scrollbar.place(relx=bar[0], rely=bar[1], relwidth=bar[2], height=bar[3])
        ot.pack(side=tk.RIGHT, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)

    def check_char(self, it, ot):
        text = it.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("找茬是吧？", "请输入需要查询的汉字！")
            return
        if len(text) != 1:
            messagebox.showwarning("找茬是吧？", "请输入单个汉字！")
            return
        if not re.match(r'[\u4e00-\u9fff\u3400-\u4dbf\u3007\u2642\U00020000-\U0002A6DF]', text):
            messagebox.showwarning("你在干嘛呢？", "非汉字或超出区段（基本区及拓展A、B区）")
            return
        res = show_all_rhythm(text)
        res = convert_to_traditional(res, self.is_traditional, 's')
        ot.pack(side=tk.BOTTOM, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    load_font(os.path.join(current_dir, 'font', "LXGWWenKaiMono-Regular.ttf"))
    root.tk.call('tk', 'scaling', 2)
    ttk.Style().theme_use('vista')
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(current_state))
    app = RhythmCheckerGUI(root)
    root.mainloop()
