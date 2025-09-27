import json
import os
import re
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from opencc import OpenCC
from common import current_state


def load_ci_index(json_path):
    """读取列表形式的 ci_index（每项为 {'name': [...], 'type': [...] }）"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# noinspection PyTypeChecker
class CiPuBrowser(tk.Toplevel):
    def __init__(self, master, json_path, fonts,
                 resource_path, state,
                 origin_dir, long_dir):
        super().__init__(master)
        self.detail_frame = None
        self.is_trad = state.get('is_traditional', False)
        self.cc_s2t = OpenCC('s2t')
        self.cc_t2s = OpenCC('t2s')

        self.title("词谱查询" if not self.is_trad else "詞譜查詢")
        self.geometry('1200x800')
        self.iconbitmap(resource_path('picture', 'ei.ico'))
        self.resizable(True, True)

        # 资源与字体
        self.fonts = fonts
        self.resource_path = resource_path
        self.current_state = state
        self.origin_dir = origin_dir
        self.long_dir = long_dir

        # 排序模式 0:拼音 1:字数 2:类型(平仄换叶)+字数
        self.sort_mode = state['sort_mode']

        # 载入数据并建立索引（包含拼音集合）
        self.indexed = load_ci_index(json_path)

        # 背景图（按新窗口大小）
        img_file = (state['bg_images'][state['bg_index']]
                    if 'bg_images' in state else 'ei.jpg')
        img_path = resource_path("picture", img_file)
        bg_img = Image.open(img_path).resize((1200, 800))
        self.bg_image = ImageTk.PhotoImage(bg_img)
        self.background_label = tk.Label(self, image=self.bg_image)
        self.background_label.place(relwidth=1, relheight=1)

        # 主框架（放在背景之上）
        self.main_frame = ttk.Frame(self)
        # 用 place 放置在背景上方，留边距
        self.main_frame.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)

        # 搜索栏
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=8, fill=tk.X)
        self.search_var = tk.StringVar()
        self.search_hint = ttk.Label(search_frame,
                                     text=self.tr_text("输入词谱名/拼音："),
                                     font=fonts['default'])
        self.search_hint.pack(side=tk.LEFT)
        entry = ttk.Entry(search_frame, textvariable=self.search_var,
                          font=fonts['default'], width=40)
        entry.pack(side=tk.LEFT, padx=6)
        entry.bind("<KeyRelease>", self.update_list)

        # 列表区
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.result_box = tk.Listbox(list_frame, font=fonts['small'])
        self.result_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.result_box.bind('<Double-1>', self.open_detail)

        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.result_box.yview)
        self.result_box.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.no_result_label = ttk.Label(self.main_frame, text="", font=fonts['default'])
        self.no_result_label.pack(pady=4)

        small_font = fonts['small']
        self.sort_btn = tk.Button(self, text=self.tr_text("排序:拼音"),
                                  font=small_font, command=self.toggle_sort)
        self.sort_btn.place(relx=0.02, rely=0.95, anchor='sw')

        self.return_btn = tk.Button(self, text=self.tr_text("返回"),
                                    font=small_font, command=self.back_to_main)
        # 初始隐藏，进入详情页时显示（使用 place）
        self.return_btn.place_forget()

        self.toggle_btn = tk.Button(self, text=("简体" if self.is_trad else "繁體"),
                                    font=small_font, command=self.toggle_lang)
        self.toggle_btn.place(relx=0.98, rely=0.95, anchor='se')

        # 当前匹配集合（按当前排序与过滤）
        self.current_matched = []
        self.update_list()

    # ---------------- 繁简支持 ----------------
    def tr_text(self, txt: str) -> str:
        """根据子窗口的繁简状态返回转换后的文本"""
        if not isinstance(txt, str):
            txt = str(txt)
        changed_txt = self.cc_s2t.convert(txt) if self.is_trad else self.cc_t2s.convert(txt)
        return self.special_process(changed_txt)

    def special_process(self, text: str) -> str:
        if "葉" in text and self.is_trad:
            pattern = re.compile(r'(?<=[平中仄換　])葉|葉(?=韻)')
            text = pattern.sub('叶', text)
        if '三臺（大麴）' in text:
            text = text.replace('三臺（大麴）', '三臺（大曲）')
        return text

    def toggle_lang(self):
        self.is_trad = not self.is_trad
        # 更新按钮与提示文本
        small_font = self.fonts['small']
        self.toggle_btn.config(text=("简体" if self.is_trad else "繁體"), font=small_font)
        self.sort_btn.config(text=self.tr_text(self.sort_label()))
        self.search_hint.config(text=self.tr_text("输入词谱名/拼音："))
        self.return_btn.config(text=self.tr_text("返回"))
        # 刷新列表显示（名称/信息需要转换）
        self.update_list()

    # ---------------- 排序 ----------------
    def sort_label(self):
        return ["排序:拼音", "排序:字数", "排序:类型"][self.sort_mode]

    def toggle_sort(self):
        self.sort_mode = (self.sort_mode + 1) % 3
        current_state['sort_mode'] = self.sort_mode
        # 更新按钮文本（tr_text 会根据当前 is_trad 转换）
        self.sort_btn.config(text=self.tr_text(self.sort_label()))
        self.update_list()

    # ---------------- 列表刷新 ----------------
    def update_list(self, _=None):
        key = self.search_var.get().strip().lower()
        self.result_box.delete(0, tk.END)

        # 排序键函数
        def sort_key(ci_pais):
            t = ci_pais['type']
            if self.sort_mode == 0:
                # ① 按拼音
                return ci_pais['full']
            elif self.sort_mode == 1:
                # ② 按字数
                return t[1]  # 已确认是 int
            else:
                # ③ 按“平/仄/换/叶”分组，再按字数，再按拼音
                order_map = {'平': 0, '仄': 1, '换': 2, '叶': 3}
                order_val = order_map[t[-1]]
                num = t[1]
                return order_val, num, ci_pais['full']

        ordered = sorted(self.indexed, key=sort_key)

        # 过滤：汉字子串匹配（主名和别名）或拼音匹配（全拼或首字母拼）
        matched = []
        if key:
            for item in ordered:
                names_lower = [n.lower() for n in item['names']]
                if any(key in n for n in names_lower):
                    matched.append(item)
                    continue
                if any(key in p for p in item['pinyins']):
                    matched.append(item)
        else:
            matched = ordered

        self.current_matched = matched

        if not matched:
            self.no_result_label.config(text=self.tr_text("找不到符合条件的词谱"))
            return
        else:
            self.no_result_label.config(text="")

        # 插入显示文本： 名称 + 若干全角空格(\u3000) + 信息（用 type 列表的各部分）
        for item in matched:
            main_name = item['names'][0] if item['names'] else ''
            nm = self.tr_text(main_name)
            tparts = item.get('type', [])
            info_parts = [str(p) for p in tparts]
            info_text = self.tr_text('\u3000'.join(part for part in info_parts))
            fill = max(0, 8 - len(nm))
            space = "\u3000" * fill
            display = nm + space + info_text
            self.result_box.insert(tk.END, display)

    # ---------------- 详情页 ----------------
    def open_detail(self, _=None):
        sel = self.result_box.curselection()
        if not sel:
            return
        idx_in_matched = sel[0]
        item = self.current_matched[idx_in_matched]
        self.show_detail(item)

    def show_detail(self, item):
        # 隐藏主列表
        self.main_frame.place_forget()

        # 显示返回按钮（放在背景上）
        small_font = self.fonts['small']
        self.return_btn.place(relx=0.5, rely=0.95, anchor='s')
        self.return_btn.config(font=small_font, text=self.tr_text("返回"))

        # 详情区（同样用 place 放在背景上）
        detail = ttk.Frame(self)
        detail.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)

        ttk.Label(detail, text=self.tr_text(item['names'][0]),
                  font=self.fonts['bigger']).pack(pady=6)

        btn_frame = ttk.Frame(detail)
        btn_frame.pack(pady=6)

        # 文本区：水平与垂直滚动条
        text_frame = ttk.Frame(detail)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        x_scroll = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        y_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_area = tk.Text(text_frame, wrap=tk.NONE, font=self.fonts['small'])
        text_area.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        x_scroll.config(command=text_area.xview)
        y_scroll.config(command=text_area.yview)
        text_area.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # 读取对应文件（依据 item['idx']）
        idx = item['idx']
        qin_path = os.path.join(self.origin_dir, f"cipai_{idx}.txt")
        long_path = os.path.join(self.long_dir, f"cipai_{idx}_long.txt")

        def read_file(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return None

        qin_text = read_file(qin_path)
        long_text = read_file(long_path)
        if isinstance(qin_text, str):
            qin_text = self.tr_text(qin_text)
        if isinstance(long_text, str):
            long_text = self.tr_text(long_text)

        def show_qin():
            text_area.config(state=tk.NORMAL)
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.END, qin_text)
            text_area.config(state=tk.DISABLED)

        def show_long():
            if long_text is None:
                return
            text_area.config(state=tk.NORMAL)
            text_area.delete('1.0', tk.END)
            text_area.insert(tk.END, long_text)
            text_area.config(state=tk.DISABLED)

        # 按钮使用小号字体
        tk.Button(btn_frame, text=self.tr_text("钦谱"), font=small_font,
                  command=show_qin).pack(side=tk.LEFT, padx=6)
        if long_text is not None:
            tk.Button(btn_frame, text=self.tr_text("龙谱"), font=small_font,
                      command=show_long).pack(side=tk.LEFT, padx=6)

        show_qin()
        # 保存 detail frame 引用以便返回销毁
        self.detail_frame = detail

    # ---------------- 返回主列表 ----------------
    def back_to_main(self):
        if hasattr(self, 'detail_frame'):
            self.detail_frame.destroy()
            del self.detail_frame

        # 隐藏返回按钮
        self.return_btn.place_forget()
        # 重新显示主列表
        self.main_frame.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)
        # 刷新（确保排列/繁简保持一致）
        self.update_list()
