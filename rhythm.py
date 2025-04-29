"""凑韵诗词格律检测工具主体tk模块，支持简体/繁体切换，使用方法请参照README文件。"""

import re
import os
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
from PIL import Image, ImageTk
from opencc import OpenCC

from common import show_all_rhythm, current_dir
from shi_rhythm import real_shi
from ci_rhythm import real_ci


def load_font(font_path):
    ctypes.windll.gdi32.AddFontResourceW(font_path)


load_font(os.path.abspath("./font/LXGWWenKaiMono-Regular.ttf"))
ico_path = os.path.join(current_dir, 'picture', 'ei.ico')
jpg_path = os.path.join(current_dir, 'picture', 'ei.jpg')
hanzi_path = os.path.join(current_dir, 'all_hanzi36133.txt')
with open(hanzi_path, 'r', encoding='utf-8') as file:
    allowed_hanzi = set(file.read())
if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        ctypes.windll.user32.SetProcessDPIAware()


def extract_chinese(text: str, comma_remain=False) -> str:
    """删除输入文本中的非汉字部分以及括号内的部分"""
    text = re.sub(r'[(（].*?[)）]', '', text)
    if not comma_remain:
        text = ''.join([char for char in text if char in allowed_hanzi]).replace('\n', '')
    else:
        comma_set = {',', '.', '?', '!', ':', "，", "。", "？", "！", "、", "："}
        text = ''.join([char for char in text if char in allowed_hanzi | comma_set]).replace('\n', '')
    return text


def convert_to_traditional(text, is_traditional, mode):
    """如果在繁体界面下转换，需要将除了诗歌以外的内容转换为繁体。"""
    if not is_traditional:
        return text
    cc = OpenCC('s2t')
    lines = text.split('\n')
    converted_lines = []
    for line in lines:
        if '\t' in line and "你的格式" not in line:
            parts = line.split('\t', 1)
            word_part = parts[0]
            non_word_part = parts[1] if len(parts) > 1 else ''
            converted_non_word = cc.convert(non_word_part)
            converted_line = f"{word_part}\t{converted_non_word}"
        elif ' ' in line and "你的格式" not in line:
            parts = line.split(' ', 1)
            word_part = parts[0]
            non_word_part = parts[1] if len(parts) > 1 else ''
            converted_non_word = cc.convert(non_word_part)
            converted_line = f"{word_part} {converted_non_word}"
        elif '在：' in line and mode == 's':
            converted_line = line
        else:
            converted_line = cc.convert(line)
        converted_lines.append(converted_line)
    converted_text = '\n'.join(converted_lines)
    # 在这里处理会被错误转换的繁体字
    converted_text = converted_text.replace('鹹韻', "咸韻")
    converted_text = converted_text.replace('十五鹹', "十五咸")
    return converted_text


def load_background_image(image_path):
    """加载并调整背景图片大小"""
    image = Image.open(image_path)
    image = image.resize((1200, 900), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def settings(mode):
    """根据模式调整窗口大小"""
    if mode in ['p', 'c']:
        return 34, 66, 8, 5
    return 15, 47, 8, 5


# noinspection PyTypeChecker
class RhythmCheckerGUI:
    def __init__(self, roots):
        self.yunshu_var = None
        self.opencc_s2t = OpenCC('s2t')
        self.opencc_t2s = OpenCC('t2s')
        self.is_traditional = False
        self.widgets_to_translate = []
        self.comboboxes = []

        self.yun_shu_map = {1: '平水韵', 2: '中华通韵', 3: '中华新韵'}
        self.initial_reverse_map = {v: k for k, v in self.yun_shu_map.items()}
        self.current_yun_shu = 1

        self.small_font = ("霞鹜文楷等宽", 12)
        self.default_font = ("霞鹜文楷等宽", 14)
        self.bigger_font = ("霞鹜文楷等宽", 16)
        self.my_purple = "#c9a6eb"

        self.cipai_form = None
        self.scrollbar = None
        self.root = roots
        self.root.iconbitmap(ico_path)
        self.root.resizable(width=False, height=False)
        self.root.title("凑韵")
        self.root.geometry("1200x900")

        self.background_image = load_background_image(jpg_path)
        self.bg_images = ["ei.jpg", "ei_2.jpg", "ei_3.jpg"]
        self.bg_index = 0
        self.background_label = tk.Label(self.root, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)
        self.cover_button = tk.Button(self.root, text="更换封面", command=self.switch_background, font=self.small_font)
        self.cover_button.place(relx=0.01, rely=0.99, anchor='sw')

        self.toggle_button = tk.Button(self.root, text="繁體", command=self.toggle_language, font=self.small_font)
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
            new = self.opencc_s2t.convert(orig) if not self.is_traditional else self.opencc_t2s.convert(orig)
            widget.config(text=new)
        for cb in self.comboboxes:
            if not self.is_traditional:
                trad_map = {k: self.opencc_s2t.convert(v) for k, v in self.yun_shu_map.items()}
                cb['values'] = [trad_map[k] for k in sorted(trad_map)]
                cb.set(trad_map[self.current_yun_shu])
            else:
                cb['values'] = [self.yun_shu_map[k] for k in sorted(self.yun_shu_map)]
                cb.set(self.yun_shu_map[self.current_yun_shu])
        # 切换按钮、标题文本
        btn_text = '简体' if not self.is_traditional else '繁體'
        self.toggle_button.config(text=btn_text)
        change_text = '切換封面' if not self.is_traditional else '切换封面'
        self.cover_button.config(text=change_text)
        title_text = '凑韵' if self.is_traditional else '湊韻'
        self.root.title(title_text)
        self.is_traditional = not self.is_traditional

    def switch_background(self):
        self.bg_index = (self.bg_index + 1) % len(self.bg_images)
        image_path = os.path.join(current_dir, "picture", self.bg_images[self.bg_index])
        self.background_image = load_background_image(image_path)
        self.background_label.config(image=self.background_image)

    def create_main_interface(self):
        self.main_interface = ttk.Frame(self.root)
        self.main_interface.pack(pady=200)

        title_label = ttk.Label(self.main_interface, text="凑韵诗词格律校验工具", font=self.bigger_font)
        title_label.pack(pady=10)
        self.register(title_label)

        frame = ttk.Frame(self.main_interface)
        frame.pack(pady=10)

        poem_button = tk.Button(frame, text="诗校验", command=self.open_poem_interface,
                                font=self.default_font, bg=self.my_purple, width=20)
        poem_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(poem_button)

        ci_button = tk.Button(frame, text="词校验", command=self.open_ci_interface,
                              font=self.default_font, bg=self.my_purple, width=20)
        ci_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(ci_button)

        char_button = tk.Button(frame, text="查字", command=self.open_char_interface,
                                font=self.default_font, bg=self.my_purple, width=20)
        char_button.pack(side=tk.TOP, padx=5, pady=10)
        self.register(char_button)

    def create_generic_interface(self, title_text, hint_text, button_text, command_func, mode):
        # 记录当前需要翻译控件数
        old_widgets = len(self.widgets_to_translate)
        old_comboboxes = len(self.comboboxes)

        self.main_interface.pack_forget()
        generic = ttk.Frame(self.root)
        generic.pack(pady=150 if mode == 's' else 50 if mode == 'c' else 100)

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
                     font=self.default_font)
        it.pack(side=tk.TOP if mode == 's' else tk.LEFT, padx=5)

        ot = tk.Text(mf, width=settings(mode)[1], height=10,
                     font=self.default_font, wrap=tk.NONE, state=tk.DISABLED)
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

    def on_yunshu_change(self):
        self.current_yun_shu = self.yunshu_reverse_map[self.yunshu_var.get()]

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
        if not text:
            title, msg = "找茬是吧？", "请输入需要校验的诗！"
            if self.is_traditional:
                title = self.opencc_s2t.convert(title)
                msg = self.opencc_s2t.convert(msg)
            messagebox.showwarning(title, msg)
            return
        processed = extract_chinese(text)
        length = len(processed)
        if (length % 10 != 0 and length % 14 != 0) or length < 20:
            messagebox.showwarning("要不检查下？", f"诗的字数不正确，你输入了{length}字")
            it.delete("1.0", tk.END)
            it.insert(tk.END, processed)
            return
        res = real_shi(self.current_yun_shu, processed)
        res = convert_to_traditional(res, self.is_traditional, 'p')
        self.scrollbar.place(relx=0.98, rely=0.14, relwidth=0.02, height=340)
        ot.pack(side=tk.RIGHT, padx=5)
        ot.config(state=tk.NORMAL)
        ot.delete("1.0", tk.END)
        ot.insert(tk.END, res)
        ot.config(state=tk.DISABLED)

    def check_ci(self, it, ot):
        text = it.get("1.0", tk.END).strip()
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
        res = convert_to_traditional(res, self.is_traditional, 'c')
        self.scrollbar.place(relx=0.41, rely=0.96, relwidth=0.59, height=20)
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
        if not re.match(r'[\u4e00-\u9fff\u3400-\u4dbf\u3007\U00020000-\U0002A6DF]', text):
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
    root.tk.call('tk', 'scaling', 2)
    ttk.Style().theme_use('vista')
    app = RhythmCheckerGUI(root)
    root.mainloop()
