"""凑韵诗词格律检测工具主体tk模块，使用方法请参照README文件。"""

import re
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from common import show_all_rhythm, current_dir
from shi_rhythm import real_shi
from ci_rhythm import real_ci

ico_path = os.path.join(current_dir, 'picture', 'ei.ico')
png_path = os.path.join(current_dir, 'picture', 'ei.png')
hanzi_path = os.path.join(current_dir, 'all_hanzi19355.txt')
with open(hanzi_path, 'r', encoding='utf-8') as file:
    allowed_hanzi = set(file.read())


def extract_chinese_and_remove_parentheses(text: str) -> str:
    """删除输入文本中的非汉字部分以及括号内的部分"""
    text_without_parentheses = re.sub(r'[(（].*?[)）]', '', text)
    return ''.join([char for char in text_without_parentheses if char in allowed_hanzi])


def load_background_image(image_path):
    """加载并调整背景图片大小"""
    image = Image.open(image_path)
    image = image.resize((800, 531), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(image)


def settings(mode):
    """根据模式调整窗口大小"""
    if mode == 'p':
        return 30, 40, 7, 5
    if mode == 'c':
        return 30, 70, 7, 5
    return 15, 30, 7, 5


class RhythmCheckerGUI:
    """
        诗词格律检测工具的图形用户界面。
        基于Tkinter，允许用户进行诗、词的格律校验以及单个汉字的查询。
        提供了直观的输入输出界面，并支持不同的韵书选择。

        Attributes:
            root (tk.Tk): Tkinter主窗口对象。
            background_image (ImageTk.PhotoImage): 背景图片。
            background_label (tk.Label): 用于显示背景图片的标签。
            current_yun_shu (int): 当前选择的韵书编号。
            input_text (tk.Text): 输入文本框组件。
            output_text (tk.Text): 输出文本框组件。
            main_interface (ttk.Frame): 主界面框架。
            cipai_var (tk.StringVar): 词牌。
            cipai_form (tk.StringVar): 输入的词牌格式
            yunshu_var (tk.StringVar): 韵书选择的变量绑定。
            yun_shu_combobox (dict): 韵书选项的映射字典。
            scrollbar_x (ttk.Scrollbar): 水平滚动条组件。
            default_font (tuple): 常规格式
            bigger_font(tuple): 大号格式
            my_purple: 选择的紫色色号

        Methods:
            create_main_interface(): 创建主界面布局。
            create_generic_interface(title_text, hint_text, button_text, command_func, mode): 创建通用的校验界面。
            on_yunshu_change(): 处理韵书选择变化的回调函数。
            open_poem_interface(): 打开诗校验界面。
            open_ci_interface(): 打开词校验界面。
            open_char_interface(): 打开查字界面。
            return_to_main(): 返回主界面。
            check_poem(input_text, output_text): 对输入的诗进行格律校验。
            check_ci(input_text, output_text): 对输入的词进行格律校验。
            check_char(input_text, output_text): 对输入的汉字进行查询。
    """
    def __init__(self, roots):
        self.cipai_form = None
        self.scrollbar_x = None
        self.root = roots
        self.root.iconbitmap(ico_path)
        self.root.resizable(width=False, height=False)
        self.root.title("凑韵")
        self.root.geometry("800x531")
        self.background_image = load_background_image(png_path)
        # noinspection PyTypeChecker
        self.background_label = tk.Label(self.root, image=self.background_image)
        self.background_label.place(relwidth=1, relheight=1)
        self.current_yun_shu = None
        self.input_text = None
        self.output_text = None
        self.main_interface = None
        self.cipai_var = None
        self.yunshu_reverse_map = None
        self.yunshu_var = None
        self.yun_shu_combobox = {1: '平水韵', 2: '中华通韵', 3: "中华新韵"}
        self.default_font = ("微软雅黑", 12)
        self.bigger_font = ("微软雅黑", 16)
        self.my_purple = "#c9a6eb"
        self.create_main_interface()

    def create_main_interface(self):
        self.main_interface = ttk.Frame(self.root)
        self.main_interface.pack(pady=100)
        title_label = ttk.Label(self.main_interface, text="凑韵诗词格律校验工具", font=self.bigger_font)
        title_label.pack(pady=10)
        button_frame = ttk.Frame(self.main_interface)
        button_frame.pack(pady=10)
        poem_button = tk.Button(button_frame, text="诗校验", command=self.open_poem_interface, font=self.default_font,
                                bg=self.my_purple, width=20)
        poem_button.pack(side=tk.TOP, padx=5, pady=10)
        ci_button = tk.Button(button_frame, text="词校验", command=self.open_ci_interface, font=self.default_font,
                              bg=self.my_purple, width=20)
        ci_button.pack(side=tk.TOP, padx=5, pady=10)
        check_char_button = tk.Button(button_frame, text="查字", command=self.open_char_interface,
                                      font=self.default_font, bg=self.my_purple, width=20)
        check_char_button.pack(side=tk.TOP, padx=5, pady=10)

    def create_generic_interface(self, title_text, hint_text, button_text, command_func, mode):
        self.main_interface.pack_forget()
        generic_interface = ttk.Frame(self.root)
        generic_interface.pack(pady=60 if mode == 's' else 20)
        title_label = ttk.Label(generic_interface, text=title_text, font=self.bigger_font)
        title_label.pack(pady=10)
        if mode != 's':
            if mode == 'c':
                self.yun_shu_combobox[1] = '词林正韵'
            else:
                self.yun_shu_combobox[1] = '平水韵'
            yunshu_frame = ttk.Frame(generic_interface)
            yunshu_frame.pack(pady=5, anchor=tk.W)
            yunshu_label = ttk.Label(yunshu_frame, text="选择韵书:", font=self.default_font)
            yunshu_label.pack(side=tk.LEFT, padx=5)
            self.yunshu_var = tk.StringVar()
            self.yunshu_var.set(self.yun_shu_combobox[1])
            yunshu_combobox = ttk.Combobox(yunshu_frame, textvariable=self.yunshu_var, font=self.default_font, width=15,
                                           state="readonly")
            yunshu_combobox['values'] = list(self.yun_shu_combobox.values())
            yunshu_combobox.pack(side=tk.LEFT, padx=5)
            self.yunshu_reverse_map = {value: key for key, value in self.yun_shu_combobox.items()}
            self.yunshu_var.trace("w", lambda name, index, the_mode: self.on_yunshu_change())
            self.current_yun_shu = 1
        if mode == 'c':
            cipai_frame = ttk.Frame(generic_interface)
            cipai_frame.pack(pady=5, anchor=tk.W)
            cipai_label = ttk.Label(cipai_frame, text="输入词牌:", font=self.default_font)
            cipai_label.pack(side=tk.LEFT, padx=5)
            self.cipai_var = tk.StringVar()
            cipai_entry = ttk.Entry(cipai_frame, textvariable=self.cipai_var, font=self.default_font, width=15)
            cipai_entry.pack(side=tk.LEFT, padx=5)
            format_frame = ttk.Frame(generic_interface)
            format_frame.pack(pady=5, anchor=tk.W)
            format_label = ttk.Label(format_frame, text="格式:", font=self.default_font)
            format_label.pack(side=tk.LEFT, padx=5)
            self.cipai_form = tk.StringVar()
            format_entry = ttk.Entry(format_frame, textvariable=self.cipai_form, font=self.default_font, width=10)
            format_entry.pack(side=tk.LEFT, padx=5)
        frame = ttk.Frame(generic_interface)
        frame.pack(pady=10)
        input_label = ttk.Label(frame, text=hint_text, font=self.default_font)
        input_label.pack(side=tk.TOP, pady=10, anchor=tk.W)
        input_text = tk.Text(frame, width=settings(mode)[0], height=1 if mode == 's' else 10, font=self.default_font)
        input_text.pack(side=tk.TOP if mode == 's' else tk.LEFT, padx=5)

        # 创建输出文本框
        output_text = tk.Text(frame, width=settings(mode)[1], height=10, font=self.default_font, wrap=tk.NONE,
                              state=tk.DISABLED)
        output_text.pack(side=tk.TOP if mode == 's' else tk.LEFT, padx=5)
        if mode == 'c':
            self.scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=output_text.xview)
            output_text.configure(xscrollcommand=self.scrollbar_x.set)
            self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            self.scrollbar_x.place(relx=0, rely=1, relwidth=1, height=0)
        button_frame = ttk.Frame(generic_interface)
        button_frame.pack(pady=10)
        analyze_button = tk.Button(button_frame, text=button_text,
                                   command=lambda: command_func(input_text, output_text), font=self.default_font,
                                   bg=self.my_purple, width=settings(mode)[2])
        analyze_button.pack(side=tk.LEFT, padx=5)
        back_button = tk.Button(button_frame, text="返回", command=self.return_to_main, font=self.default_font,
                                bg=self.my_purple, width=settings(mode)[3])
        back_button.pack(side=tk.RIGHT, padx=5)
        output_text.pack_forget()

        return input_text, output_text

    def on_yunshu_change(self):
        selected_yunshu = self.yunshu_var.get()
        self.current_yun_shu = self.yunshu_reverse_map[selected_yunshu]

    def open_poem_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="诗校验",
            hint_text='请输入需要分析的律诗或绝句：',
            button_text="开始分析",
            command_func=self.check_poem,
            mode='p'
        )

    def open_ci_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="词校验",
            hint_text='请输入需要分析的词：',
            button_text="开始分析",
            command_func=self.check_ci,
            mode='c'
        )

    def open_char_interface(self):
        self.input_text, self.output_text = self.create_generic_interface(
            title_text="查字",
            hint_text='请输入需要查询的汉字：',
            button_text="开始查询",
            command_func=self.check_char,
            mode='s'
        )

    def return_to_main(self):
        for widget in self.root.winfo_children():
            if widget != self.main_interface:
                widget.pack_forget()
        self.main_interface.pack(pady=100)

    def check_poem(self, input_text, output_text):
        text = input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("找茬是吧", "请输入需要校验的诗！")
            return
        processed_text = extract_chinese_and_remove_parentheses(text)
        len_shi = len(processed_text)
        if len_shi % 10 != 0 and len_shi % 14 != 0 or len_shi < 20:
            print(len_shi)
            messagebox.showwarning("要不检查下？", f"诗的字数不正确，可能有无法识别的生僻字，你输入了{len_shi}字")
            input_text.delete("1.0", tk.END)
            input_text.insert(tk.END, processed_text)
            return
        else:
            result = real_shi(self.current_yun_shu, processed_text)
            output_text.pack(side=tk.RIGHT, padx=5)
            output_text.config(state=tk.NORMAL)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, result)
            output_text.config(state=tk.DISABLED)

    def check_ci(self, input_text, output_text):
        text = input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("找茬是吧", "请输入需要校验的词！")
            return
        cipai = self.cipai_var.get().strip()
        form = self.cipai_form.get().strip()
        if not cipai:
            messagebox.showwarning("找茬是吧", "请输入词牌！")
            return
        processed_text = extract_chinese_and_remove_parentheses(text)
        len_ci = len(processed_text)
        result = real_ci(self.current_yun_shu, cipai, processed_text, form)
        if result == 0:
            messagebox.showwarning("要不检查下？", "不能找到你输入的词牌！")
        elif result == 1:
            messagebox.showwarning("要不检查下？", f"内容无法匹配词牌格式，请检查格式以及是否有无法识别的生僻字！\n你输入了{len_ci}字！")
        elif result == 2:
            messagebox.showwarning('找茬是吧？', "输入的格式不正确，请输入正确的格式数字！")
        else:
            self.scrollbar_x.place(relx=0.35, rely=0.94, relwidth=0.65, height=20)
            output_text.pack(side=tk.RIGHT, padx=5)
            output_text.config(state=tk.NORMAL)
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, result)
            output_text.config(state=tk.DISABLED)

    @staticmethod
    def check_char(input_text, output_text):
        text = input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("找茬是吧", "请输入需要查询的汉字！")
            return
        if len(text) != 1:
            messagebox.showwarning("找茬是吧", "请输入单个汉字！")
            return
        if not re.match(r'[\u4e00-\u9fff\u3400-\u4dbf]', text):
            messagebox.showwarning("你在干嘛呢", "输入的内容非汉字或其不在基本区及拓展A区")
            return
        result = show_all_rhythm(text)
        output_text.pack(side=tk.BOTTOM, padx=5)
        output_text.config(state=tk.NORMAL)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, result)
        output_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = RhythmCheckerGUI(root)
    root.mainloop()
