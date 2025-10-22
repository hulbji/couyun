import json
import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


def load_ci_index(json_path):
    """读取列表形式的 ci_index（每项为 {'name': [...], 'type': [...] }）"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# noinspection PyTypeChecker
class CiPuBrowser(tk.Toplevel):
    _instance = None

    def __init__(self, master, json_path, fonts, resource_path,
                 state, origin_dir, long_dir, origin_trad_dir, long_trad_dir, current_state):
        if CiPuBrowser._instance is not None and CiPuBrowser._instance.winfo_exists():
            CiPuBrowser._instance.lift()
            return
        if CiPuBrowser._instance is not None:
            CiPuBrowser._instance.destroy()

        super().__init__(master)

        self.detail_text = None
        self.current_show = 'qin'
        self.long_raw = None
        self.qin_raw = None
        self.detail_frame = None
        self.detail_title = None
        self.qin_btn = None
        self.long_btn = None
        self.btn_frame = None

        self.qin_raw_s = None
        self.qin_raw_t = None
        self.long_raw_s = None
        self.long_raw_t = None
        self.current_item = None
        self.current_state = current_state

        self.is_trad = state.get('is_traditional', False)

        self.title("詞譜查詢" if self.is_trad else "词谱查询")
        base_size = [860, 645]
        self.scale = 1.5
        scaled_size = [int(base_size[0] * self.scale), int(base_size[1] * self.scale)]
        self.geometry(f'{scaled_size[0]}x{scaled_size[1]}')
        self.iconbitmap(resource_path('picture', 'ei.ico'))
        self.resizable(False, False)
        self.fonts = fonts
        self.resource_path = resource_path
        self.current_state = state
        self.origin_dir = origin_dir
        self.long_dir = long_dir
        self.origin_trad_dir = origin_trad_dir
        self.long_trad_dir = long_trad_dir
        self.sort_mode = state['sort_mode']
        self.indexed = load_ci_index(json_path)

        # 背景图（按新窗口大小）
        img_file = (state['bg_images'][state['bg_index']]
                    if 'bg_images' in state else 'ei.jpg')
        img_path = resource_path("picture", img_file)
        bg_img = Image.open(img_path).resize((scaled_size[0], scaled_size[1]))
        self.bg_image = ImageTk.PhotoImage(bg_img)
        self.background_label = tk.Label(self, image=self.bg_image)
        self.background_label.place(relwidth=1, relheight=1)

        # 主框架（放在背景之上）
        self.main_frame = ttk.Frame(self)
        self.main_frame.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)

        # 搜索栏
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(pady=8, fill=tk.X)
        self.search_var = tk.StringVar()
        self.search_hint = ttk.Label(search_frame,
                                     text="輸入詞譜名/拼音：" if self.is_trad else "输入词谱名/拼音：",
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
        self.sort_btn = tk.Button(self, text=self.sort_label(),
                                  font=small_font, command=self.toggle_sort)
        self.sort_btn.place(relx=0.02, rely=0.95, anchor='sw')

        self.return_btn = tk.Button(self, text="返回",
                                    font=small_font, command=self.back_to_main)
        self.return_btn.place_forget()

        self.toggle_btn = tk.Button(self, text=("简体" if self.is_trad else "繁體"),
                                    font=small_font, command=self.toggle_lang)
        self.toggle_btn.place(relx=0.98, rely=0.95, anchor='se')

        self.current_matched = []
        self.result_box.insert(tk.END, "")  # 触发初始化
        self.result_box.delete(0, tk.END)
        self.update_list()

    @staticmethod
    def show_ci_pu(text_area: tk.Text, raw_text: str):
        """
        在指定 Text 控件中显示词谱内容。
        raw_text 必须是未经过繁简转换的原文。
        """
        if raw_text is None:
            return
        text_area.config(state=tk.NORMAL)
        text_area.delete('1.0', tk.END)
        text_area.insert(tk.END, raw_text)
        text_area.config(state=tk.DISABLED)

    def toggle_lang(self):
        """翻转简繁状态并全局刷新：主界面 + 详情页（若已打开）"""
        # t0 = time.perf_counter()
        self.is_trad = not self.is_trad
        self.title("詞譜查詢" if self.is_trad else "词谱查询")
        self.toggle_btn.config(text="繁體" if self.is_trad else "简体",
                               font=self.fonts['small'])
        self.sort_btn.config(text=self.sort_label())
        self.search_hint.config(text="輸入詞譜名/拼音：" if self.is_trad else "输入词谱名/拼音：")
        self.return_btn.config(text="返回")
        if getattr(self, 'detail_frame', None) is not None and self.detail_frame.winfo_exists():
            self._refresh_detail_lang()
        self.update_list()
        # t1 = time.perf_counter()
        # print(f"[toggle_lang] time {t1 - t0:.3f}s")

    def _refresh_detail_lang(self):
        # t0 = time.perf_counter()
        self.qin_raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.long_raw = self.long_raw_t if self.is_trad else self.long_raw_s

        self.detail_title.config(
            text=self.current_item['names_trad'][0] if self.is_trad else self.current_item['names'][0]
        )
        self.qin_btn.config(text='欽譜' if self.is_trad else '钦谱',
                            command=self._on_qin)
        if self.long_btn is not None:
            self.long_btn.config(text='龍譜' if self.is_trad else '龙谱',
                                 command=self._on_long)

        raw = self.qin_raw if self.current_show == 'qin' else self.long_raw
        self.show_ci_pu(self.detail_text, raw)
        # t1 = time.perf_counter()
        # print(f"[_refresh_detail_lang] time {t1 - t0:.3f}s")

    def sort_label(self):
        return ["排序:拼音", "排序:字數", "排序:類型"][self.sort_mode] if self.is_trad else \
        ["排序:拼音", "排序:字数", "排序:类型"][self.sort_mode]

    def toggle_sort(self):
        self.sort_mode = (self.sort_mode + 1) % 3
        self.current_state['sort_mode'] = self.sort_mode
        self.sort_btn.config(text=self.sort_label())
        self.update_list()

    def update_list(self, _=None):
        # t0 = time.perf_counter()
        key = self.search_var.get().strip().lower()
        self.result_box.delete(0, tk.END)
        # t1 = time.perf_counter()

        def sort_key(ci_pais):
            t = ci_pais['type']
            if self.sort_mode == 0:
                return ci_pais['full']
            elif self.sort_mode == 1:
                return t[1]  # 已确认是 int
            else:
                order_map = {'平': 0, '仄': 1, '换': 2, '叶': 3}
                order_val = order_map[t[-1][0]]
                num = t[1]
                return order_val, num, ci_pais['full']

        ordered = sorted(self.indexed, key=sort_key)
        # t2 = time.perf_counter()

        matched = []
        if key:
            for item in ordered:
                if any(key in n for n in item['names']) or any(key in p for p in item['pinyins']):
                    matched.append(item)
        else:
            matched = ordered

        self.current_matched = matched

        if not matched:
            self.no_result_label.config(text="找不到符合條件的詞譜"if self.is_trad else "找不到符合条件的词谱")
            return
        else:
            self.no_result_label.config(text="")
        # t3 = time.perf_counter()

        displays = [it['display_t'] if self.is_trad else it['display_s'] for it in matched]

        self.result_box.pack_forget()
        self.result_box.delete(0, tk.END)
        self.result_box.insert(tk.END, *displays)
        self.result_box.update_idletasks()
        self.result_box.pack(fill='both', expand=True)

        # t4 = time.perf_counter()
        # print(f"[update_list] time {t1 - t0:.3f}s {t2 - t1:.3f}s {t3 - t2:.3f}s {t4 - t3:.3f}s")
        # print(f"[update_list] displays count: {len(displays)}")

    def open_detail(self, _=None):
        sel = self.result_box.curselection()
        if not sel:
            return
        idx_in_matched = sel[0]
        item = self.current_matched[idx_in_matched]
        self.show_detail(item)

    @staticmethod
    def read_file(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    # ---------- 拆分后的三个函数 ----------
    def load_ci_files(self, item):
        """
        根据 idx 一次性把 4 个文件读出来，返回 dict。
        键：qin_raw_s / qin_raw_t / long_raw_s / long_raw_t
        读不到返回 None。
        """
        idx = item['idx']
        return {
            'qin_raw_s': self.read_file(os.path.join(self.origin_dir, f'cipai_{idx}.txt')),
            'qin_raw_t': self.read_file(os.path.join(self.origin_trad_dir, f'cipai_{idx}_trad.txt')),
            'long_raw_s': self.read_file(os.path.join(self.long_dir, f'cipai_{idx}_long.txt')),
            'long_raw_t': self.read_file(os.path.join(self.long_trad_dir, f'cipai_{idx}_long_trad.txt')),
        }

    def _on_qin(self):
        self.current_show = 'qin'
        raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.show_ci_pu(self.detail_text, raw)

    def _on_long(self):
        self.current_show = 'long'
        raw = self.long_raw_t if self.is_trad else self.long_raw_s
        self.show_ci_pu(self.detail_text, raw)

    def show_detail_body(self, detail, text_area, btn_frame, files_dict):
        """
        根据已读到的文件内容，完成：
        1. 按当前繁/简模式给 self.qin_raw / self.long_raw 赋值
        2. 创建“钦谱/龙谱”按钮并绑定事件
        3. 默认显示钦谱
        """
        small_font = self.fonts['small']

        # 按当前模式选取简体 or 繁体
        self.qin_raw_s = files_dict['qin_raw_s']
        self.qin_raw_t = files_dict['qin_raw_t']
        self.long_raw_s = files_dict['long_raw_s']
        self.long_raw_t = files_dict['long_raw_t']
        self.qin_raw = self.qin_raw_t if self.is_trad else self.qin_raw_s
        self.long_raw = self.long_raw_t if self.is_trad else self.long_raw_s

        # 钦谱按钮
        self.qin_btn = tk.Button(btn_frame,
                  text='欽譜' if self.is_trad else '钦谱',
                  font=small_font,
                  command=self._on_qin
                  )
        self.qin_btn.pack(side=tk.LEFT, padx=int(4*self.scale))

        # 龙谱按钮（有内容才显示）
        if self.long_raw is not None:
            self.long_btn = tk.Button(btn_frame,
                      text='龍譜' if self.is_trad else '龙谱',
                      font=small_font,
                      command=self._on_long
                      )
            self.long_btn.pack(padx=int(4*self.scale))

        # 默认显示钦谱
        self.show_ci_pu(text_area, self.qin_raw)
        # 把 detail 保存到实例变量，方便返回按钮销毁
        self.detail_frame = detail

    def show_detail(self, item):
        """原函数只保留界面骨架，逻辑部分通过上面两个新函数完成。"""
        # t0 = time.perf_counter()
        self.main_frame.place_forget()
        self.sort_btn.place_forget()
        self.current_item = item

        small_font = self.fonts['small']
        self.return_btn.place(relx=0.5, rely=0.95, anchor='s')
        self.return_btn.config(font=small_font, text="返回")

        detail = ttk.Frame(self)
        detail.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)

        self.detail_title = ttk.Label(detail,
                  text=item['names_trad'][0] if self.is_trad else item['names'][0],
                  font=self.fonts['bigger'])
        self.detail_title.pack(pady=6)

        self.btn_frame = ttk.Frame(detail)
        self.btn_frame.pack(pady=6)

        text_frame = ttk.Frame(detail)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        y_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_area = tk.Text(text_frame, wrap=tk.CHAR, font=self.fonts['small'])
        text_area.configure(yscrollcommand=y_scroll.set)
        self.detail_text = text_area
        y_scroll.config(command=text_area.yview)

        text_area.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")

        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        files_dict = self.load_ci_files(item)
        self.show_detail_body(detail, text_area, self.btn_frame, files_dict)
        self.current_show = 'qin'
        # t1 = time.perf_counter()
        # print(f"[show_detail] time {t1 - t0:.3f}s")

    # ---------------- 返回主列表 ----------------
    def back_to_main(self):
        if hasattr(self, 'detail_frame'):
            self.qin_btn = None
            self.long_btn = None
            self.detail_frame.destroy()
            del self.detail_frame

        # 清理与详情页相关的属性
        for attr in ('detail_text', 'qin_raw', 'long_raw', 'current_show'):
            if hasattr(self, attr):
                delattr(self, attr)

        self.sort_btn.place(relx=0.02, rely=0.95, anchor='sw')
        self.return_btn.place_forget()
        self.main_frame.place(relx=0.02, rely=0.03, relwidth=0.96, relheight=0.82)
        self.update_list()
