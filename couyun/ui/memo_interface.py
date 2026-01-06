import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import logging
import traceback

memo_logger = logging.getLogger("RhythmChecker.MemoInterface")
memo_logger.setLevel(logging.INFO)

def log_memo_exceptions(func):
    """记录备忘录操作的装饰器（和词谱浏览器日志逻辑一致）"""
    def _memo_interface(self, *args, **kwargs):
        func_name = func.__name__
        try:
            result = func(self, *args, **kwargs)
            memo_logger.info(f"【{func_name}】正常完成")
            return result
        except Exception as e:
            memo_logger.error(f"【{func_name}】发生异常: {str(e)}")
            memo_logger.error(traceback.format_exc())
            raise
    return _memo_interface


# noinspection PyTypeChecker
class MemoInterface(tk.Toplevel):
    def __init__(self, master, fonts, resource_path, is_trad):

        self.widgets_to_translate = []
        self.s2t = str.maketrans("个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
                                 "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验",
                                 "个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
                                 "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗")
        self.t2s = str.maketrans("个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
                                 "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗",
                                 "个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
                                 "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验")
        super().__init__(master.root)

        self.fonts = fonts
        self.resource_path = resource_path
        self.is_trad = is_trad
        self.main_app = master

        self.data_path = os.path.join(os.path.dirname(resource_path()), './assets/state/memo_data.json')

        self.title("備忘錄" if is_trad else "备忘录")
        self.geometry("1000x1100")
        self.resizable(False, False)

        self.notes = []
        self.categories = ["诗词", "摘抄"]
        self.default_category = "默认"
        self.current_filter = "全部"
        self.search_keyword = ""
        self.sort_mode = "时间倒序"
        self.current_note_id = None
        self.current_displayed_notes = []

        self.export_selected_ids = set()
        self.export_path = os.getcwd()

        self.toggle_btn = None
        self.main_frame = None
        self.detail_frame = None
        self.search_var = None
        self.filter_var = None
        self.filter_combo = None
        self.sort_var = None
        self.notes_listbox = None
        self.new_btn_main = None
        self.status_var = None
        self.status_bar = None
        self.title_var = None
        self.category_var = None
        self.category_combo = None
        self.content_text = None
        self.cat_listbox = None
        self.export_listbox = None
        self.export_filter_combo = None
        self.export_filter_var = None
        self.select_all_var = None
        self.export_manager_window = None
        self.export_path_label = None
        self.export_path_var = None
        self.validate_choice_window = None
        self._status_clear = None
        self.export_manager_window = None
        self.category_manager_window = None
        self.validate_choice_window = None
        self.manager = None

        self.load_data()
        self.create_ui()
        self.show_list_view()
        self.after_idle(self._post_ui_init)

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    @ log_memo_exceptions
    def _post_ui_init(self):
        """
        UI 已经显示后，再执行的慢操作
        """
        self.refresh_notes_list()
        self.update_status("")

    def memo_register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    @log_memo_exceptions
    def toggle_language(self):
        """在简体和繁体之间切换（注意：使用目标模式来渲染）"""
        to_trad = not self.is_trad  # 目标模式
        for widget in self.widgets_to_translate:
            try:
                if widget and hasattr(widget, 'w') and widget.w:
                    orig = widget.cget('text')
                    new_text = self.cc_convert(orig, to_trad)
                    widget.config(text=new_text)
            except:
                continue

        title_text = "备忘录" if self.is_trad else "備忘錄"
        self.title(title_text)
        btn_text = '繁體' if self.is_trad else '简体'
        self.toggle_btn.config(text=btn_text)
        self.is_trad = to_trad

    @log_memo_exceptions
    def cc_convert(self, text, to_trad: bool):
        """根据目标模式转换文本"""
        return text.translate(self.s2t) if to_trad else text.translate(self.t2s)

    @log_memo_exceptions
    def create_ui(self):
        """创建所有UI组件（主框架和详情框架）"""
        self.main_frame = ttk.Frame(self)

        # 搜索框
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        ttk.Label(search_frame, text="搜索:", font=self.fonts['default']).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=self.fonts['default'], width=40)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        search_entry.bind('<KeyRelease>', self.on_search)

        # 筛选和排序
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 类型筛选
        type_label = ttk.Label(control_frame, text="类型:", font=self.fonts['default'])
        type_label.pack(side=tk.LEFT)
        self.memo_register(type_label)
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(control_frame, textvariable=self.filter_var,
                                    values=["全部"] + self.categories,
                                    font=self.fonts['default'], state="readonly", width=12)
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        self.filter_combo = filter_combo

        # 排序方式
        ttk.Label(control_frame, text="排序:", font=self.fonts['default']).pack(side=tk.LEFT, padx=(20, 5))
        self.sort_var = tk.StringVar(value=self.sort_mode)
        sort_combo = ttk.Combobox(control_frame, textvariable=self.sort_var,
                                  values= ["時間正序", "時間倒序", "標題", "類型"] if self.is_trad else ["时间倒序", "时间正序", "标题", "类型"],
                                  font=self.fonts['default'], state="readonly", width=12)
        sort_combo.pack(side=tk.LEFT, padx=5)
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)
        self.memo_register(sort_combo)

        # 笔记列表（添加横向滚动条）
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        x_scroll = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.notes_listbox = tk.Listbox(list_frame, font=self.fonts['default'],
                                        xscrollcommand=x_scroll.set,
                                        width=60)
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.notes_listbox.bind('<Double-1>', self.on_note_select)
        self.notes_listbox.bind(
            '<<ListboxSelect>>',
            lambda e: self.after_idle(self.on_note_select)
        )

        # 防止空白区域点击选中最后一个项目
        self.notes_listbox.bind('<Button-1>', self.on_listbox_click)

        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.notes_listbox.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.notes_listbox.config(yscrollcommand=y_scroll.set)
        x_scroll.config(command=self.notes_listbox.xview)

        # 主界面按钮
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.new_btn_main = tk.Button(btn_frame, text="+ 新建笔记" if not self.is_trad else "+ 新建筆記",
                                      command=self.show_new_note_view, font=self.fonts['default'],
                                      bg="#c9a6eb", width=12)
        self.new_btn_main.pack(side=tk.LEFT, padx=5)
        self.memo_register(self.new_btn_main)

        manage_cat_btn = tk.Button(btn_frame, text="管理类型" if not self.is_trad else "管理類型",
                                   command=self.open_category_manager, font=self.fonts['default'],
                                   width=12)
        manage_cat_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(manage_cat_btn)

        export_btn = tk.Button(btn_frame, text="导出笔记" if not self.is_trad else "導出筆記",
                               command=self.open_export_manager, font=self.fonts['default'], width=12)
        export_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(export_btn)

        self.toggle_btn = tk.Button(btn_frame, text="繁體" if not self.is_trad else "简体",
                               command=self.toggle_language, font=self.fonts['default'], width=12)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(btn_frame, text="关闭" if not self.is_trad else "關閉",
                             command=self.destroy, font=self.fonts['default'], width=12)
        back_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(back_btn)

        # === 详情框架（编辑视图）===
        self.detail_frame = ttk.Frame(self)

        # 标题栏
        title_frame = ttk.Frame(self.detail_frame)
        title_frame.pack(fill=tk.X, pady=10)

        biao_ti_frame = ttk.Label(title_frame, text="標題" if self.is_trad else "标题:", font=self.fonts['bigger'])
        biao_ti_frame.pack(side=tk.LEFT)
        self.memo_register(biao_ti_frame)
        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(title_frame, textvariable=self.title_var, font=self.fonts['bigger'])
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        lei_xing_label = ttk.Label(title_frame, text="类型:", font=self.fonts['default'])
        lei_xing_label.pack(side=tk.LEFT)
        self.memo_register(lei_xing_label)
        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(title_frame, textvariable=self.category_var,
                                      values=self.categories, font=self.fonts['default'], width=15)
        category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo = category_combo

        # 内容编辑区
        content_frame = ttk.Frame(self.detail_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.content_text = tk.Text(content_frame, font=self.fonts['default'], wrap=tk.WORD)
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 详情页进度条
        content_scroll = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=content_scroll.set)

        # 详情界面按钮
        detail_btn_frame = ttk.Frame(self.detail_frame)
        detail_btn_frame.pack(fill=tk.X, pady=10)

        save_btn = tk.Button(detail_btn_frame, text="💾 保存",
                             command=self.save_current_note, font=self.fonts['default'],
                             bg="#c9a6eb", width=12)
        save_btn.pack(side=tk.LEFT, padx=5)

        validate_btn = tk.Button(detail_btn_frame, text="🔍 校驗" if self.is_trad else "🔍 校验",
                                 command=self.open_validate_choice, font=self.fonts['default'],
                                 width=12)
        validate_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(validate_btn)

        delete_btn = tk.Button(detail_btn_frame, text="🗑️ 刪除" if self.is_trad else "🗑️ 删除",
                               command=self.delete_note, font=self.fonts['default'], width=12)
        delete_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(delete_btn)

        return_btn = tk.Button(detail_btn_frame, text="← 返回列表",
                               command=self.show_list_view, font=self.fonts['default'], width=12)
        return_btn.pack(side=tk.RIGHT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, font=self.fonts['small'])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    @log_memo_exceptions
    def open_validate_choice(self):
        """打开校验选择窗口"""
        if self.validate_choice_window is not None and self.validate_choice_window.winfo_exists():
            self.validate_choice_window.lift()
            return

        self.validate_choice_window = tk.Toplevel(self)
        self.validate_choice_window.title("选择校验类型" if not self.is_trad else "選擇校驗類型")
        self.validate_choice_window.geometry("300x200")
        self.validate_choice_window.resizable(False, False)
        self.validate_choice_window.transient(self)

        self.validate_choice_window.protocol("WM_DELETE_WINDOW",
                                             lambda: (self.validate_choice_window.destroy(),
                                                      setattr(self, 'validate_choice_window', None)))

        frame = ttk.Frame(self.validate_choice_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        poem_btn = tk.Button(frame, text="🔍 校验诗" if not self.is_trad else "🔍 校驗詩",
                             command=lambda: self.execute_validate('poem'),
                             font=self.fonts['default'], width=15, bg="#c9a6eb")
        poem_btn.pack(pady=10)
        self.memo_register(poem_btn)

        ci_btn = tk.Button(frame, text="🔍 校验词" if not self.is_trad else "🔍 校驗詞",
                           command=lambda: self.execute_validate('ci'),
                           font=self.fonts['default'], width=15, bg="#c9a6eb")
        ci_btn.pack(pady=10)
        self.memo_register(ci_btn)

    def execute_validate(self, mode):
        """执行校验"""
        content = self.content_text.get("1.0", tk.END).strip()
        self.main_app.validate_content(mode, content)
        self.validate_choice_window.destroy()

    def show_list_view(self):
        """显示主列表界面"""
        self.detail_frame.pack_forget()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.refresh_notes_list()
        self.update_status("")

    def show_detail_view(self):
        """显示详情编辑界面"""
        self.main_frame.pack_forget()
        self.detail_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def show_new_note_view(self):
        """新建笔记时调用"""
        self.current_note_id = None
        self.title_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.category_var.set(self.default_category)
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
            # 立即保存配置文件，确保下次能读到
            self.save_data()

    @log_memo_exceptions
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

    @log_memo_exceptions
    def save_current_note(self):
        """手动保存当前编辑的笔记"""
        title = self.title_var.get().strip()
        content = self.content_text.get("1.0", tk.END).strip()
        category = self.category_var.get().strip() or self.default_category

        if not title and not content:
            self.update_status("笔记为空，未保存" if not self.is_trad else "筆記為空，未保存")
            return

        if self.current_note_id is None:
            new_note = {
                'id': str(datetime.now().timestamp()),
                'title': title or "NoName",
                'content': content,
                'category': category,
                'created_time': datetime.now().isoformat(),
                'modified_time': datetime.now().isoformat()
            }
            self.notes.append(new_note)
            self.current_note_id = new_note['id']
            self.update_status("新建笔记已保存" if not self.is_trad else "新建筆記已保存")
        else:
            for note in self.notes:
                if note['id'] == self.current_note_id:
                    note['title'] = title or note['title']
                    note['content'] = content
                    note['category'] = category
                    note['modified_time'] = datetime.now().isoformat()
                    break
            self.update_status("笔记已保存" if not self.is_trad else "筆記已保存")

        self.save_data()
        self.refresh_notes_list()

    @log_memo_exceptions
    def delete_note(self):
        """删除当前笔记"""
        if not self.current_note_id:
            return

        msg = "确定要删除这条笔记吗？" if not self.is_trad else "確定要刪除這條筆記嗎？"
        if messagebox.askyesno("确认删除" if not self.is_trad else "確認刪除", msg):
            self.notes = [n for n in self.notes if n['id'] != self.current_note_id]
            self.save_data()
            self.current_note_id = None
            self.show_list_view()
            self.update_status("笔记已删除" if not self.is_trad else "筆記已刪除")

    @log_memo_exceptions
    def on_note_select(self, _=None):
        """双击笔记打开详情"""
        selection = self.notes_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if 0 <= index < len(self.current_displayed_notes):
            note = self.current_displayed_notes[index]
            self.current_note_id = note['id']
            self.title_var.set(note['title'])
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0",note['content'])
            self.category_var.set(note['category'])
            self.show_detail_view()

    @log_memo_exceptions
    def on_search(self, _):
        """搜索事件"""
        self.search_keyword = self.search_var.get().strip().lower()
        self.refresh_notes_list()

    @log_memo_exceptions
    def on_filter_change(self, _):
        """筛选变化事件"""
        self.current_filter = self.filter_var.get()
        self.refresh_notes_list()

    @log_memo_exceptions
    def on_sort_change(self, _):
        """排序变化事件"""
        self.sort_mode = self.sort_var.get()
        self.refresh_notes_list()

    @log_memo_exceptions
    def on_listbox_click(self, event):
        """处理列表点击事件，空白区域不选中最后一个项目"""
        index = self.notes_listbox.nearest(event.y)
        bbox = self.notes_listbox.bbox(index)
        if bbox is None:
            self.notes_listbox.selection_clear(0, tk.END)
            return "break"
        x, y, w, h = bbox
        if event.y < y or event.y > y + h:
            self.notes_listbox.selection_clear(0, tk.END)
            return "break"
        return None

    @log_memo_exceptions
    def get_filtered_notes(self):
        """获取筛选后的笔记"""
        filtered = self.notes
        if self.search_keyword:
            filtered = [n for n in filtered if self.search_keyword in n['title'].lower() or
                        self.search_keyword in n['content'].lower()]
        if self.current_filter != "全部":
            filtered = [n for n in filtered if n['category'] == self.current_filter]
        return filtered

    @log_memo_exceptions
    def sort_notes(self, notes):
        """排序笔记"""
        if self.sort_mode in ["时间倒序", "時間倒序"]:
            return sorted(notes, key=lambda x: x['modified_time'], reverse=True)
        elif self.sort_mode in ["时间正序", "時間正序"]:
            return sorted(notes, key=lambda x: x['modified_time'])
        elif self.sort_mode == ["标题", "標題"]:
            return sorted(notes, key=lambda x: x['title'])
        elif self.sort_mode == ["类型", "類型"]:
            return sorted(notes, key=lambda x: (x['category'], x['title']))
        return notes

    @log_memo_exceptions
    def refresh_notes_list(self):
        """刷新笔记列表显示"""
        self.notes_listbox.delete(0, tk.END)
        notes = self.get_filtered_notes()
        notes = self.sort_notes(notes)

        self.current_displayed_notes = notes

        for note in notes:
            display_text = f"{note['title'][:35]} | {note['category']} | {note['modified_time'][:10]}"
            self.notes_listbox.insert(tk.END, display_text)

    @log_memo_exceptions
    def open_category_manager(self):
        """打开分类管理窗口"""
        self.manager = tk.Toplevel(self)
        self.manager.title("管理类型" if not self.is_trad else "管理類型")
        self.manager.geometry("800x500")
        self.manager.resizable(False, False)
        self.manager.transient(self)

        list_frame = ttk.Frame(self.manager)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cat_listbox = tk.Listbox(list_frame, font=self.fonts['default'], selectmode=tk.SINGLE)
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.refresh_category_list()

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.cat_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cat_listbox.config(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(self.manager)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        add_btn = tk.Button(btn_frame, text="新建类型" if not self.is_trad else "新建類型",
                            command=self.add_category, font=self.fonts['default'], width=12)
        add_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(add_btn)

        rename_btn = tk.Button(btn_frame, text="重命名" if not self.is_trad else "重命名",
                               command=self.rename_category, font=self.fonts['default'], width=9)
        rename_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(rename_btn)

        delete_btn = tk.Button(btn_frame, text="删除" if not self.is_trad else "刪除",
                               command=self.delete_category, font=self.fonts['default'], width=6)
        delete_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(delete_btn)

        set_default_btn = tk.Button(btn_frame, text="设为默认" if not self.is_trad else "設為默認",
                                    command=self.set_default_category, font=self.fonts['default'], width=12)
        set_default_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(set_default_btn)


        close_btn = tk.Button(btn_frame, text="关闭" if not self.is_trad else "關閉",
                              command=self.manager.destroy, font=self.fonts['default'], width=6)
        close_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(close_btn)

    @log_memo_exceptions
    def refresh_category_list(self):
        """刷新分类列表显示"""
        self.cat_listbox.delete(0, tk.END)
        for cat in self.categories:
            display = cat
            if cat == self.default_category:
                display += " (默认)" if not self.is_trad else " (默認)"
            self.cat_listbox.insert(tk.END, display)

    @log_memo_exceptions
    def add_category(self):
        """添加新分类"""
        new_cat = simpledialog.askstring("新建类型" if not self.is_trad else "新建類型",
                                         "请输入新类型名称:" if not self.is_trad else "請輸入新類型名稱:")
        if new_cat and new_cat.strip():
            new_cat = new_cat.strip()
            if new_cat not in self.categories:
                self.categories.append(new_cat)
                self.save_data()
                self.refresh_category_list()
                self.update_category_lists()
                self.update_status(f"已添加类型: {new_cat}")
            else:
                if self.is_trad:
                    messagebox.showwarning("提示", "該類型已存在")
                else:
                    messagebox.showwarning("提示", "该类型已存在")

    @log_memo_exceptions
    def rename_category(self):
        """重命名分类"""
        selection = self.cat_listbox.curselection()
        if not selection:
            if self.is_trad:
                messagebox.showwarning("提示", "請先選擇一個類型")
            else:
                messagebox.showwarning("提示", "请先选择一个类型")
            return

        old_cat = self.categories[selection[0]]
        new_cat = simpledialog.askstring("重命名" if not self.is_trad else "重命名",
                                         f"将 '{old_cat}' 重命名为:" if not self.is_trad else f"將 '{old_cat}' 重命名為:",
                                         initialvalue=old_cat)
        if new_cat and new_cat.strip() and new_cat != old_cat:
            new_cat = new_cat.strip()
            self.categories[self.categories.index(old_cat)] = new_cat
            if self.default_category == old_cat:
                self.default_category = new_cat
            for note in self.notes:
                if note['category'] == old_cat:
                    note['category'] = new_cat
            self.save_data()
            self.refresh_category_list()
            self.update_category_lists()
            self.refresh_notes_list()
            self.update_status(f"已重命名: {old_cat} -> {new_cat}")

    @log_memo_exceptions
    def delete_category(self):
        """删除分类（默认分类不能删除）"""
        selection = self.cat_listbox.curselection()
        if not selection:
            if self.is_trad:
                messagebox.showwarning("提示", "請先選擇一個類型")
            else:
                messagebox.showwarning("提示", "请先选择一个类型")
            return

        cat_to_delete = self.categories[selection[0]]
        if cat_to_delete == self.default_category:
            if self.is_trad:
                messagebox.showwarning("提示", "默認類型不能刪除")
            else:
                messagebox.showwarning("提示", "默认类型不能删除")
            return

        notes_with_cat = [n for n in self.notes if n['category'] == cat_to_delete]
        msg = f"确定要删除类型 '{cat_to_delete}' 吗？" if not self.is_trad else f"確定要刪除類型 '{cat_to_delete}' 嗎？"
        if notes_with_cat:
            if self.is_trad:
                msg += f"\n\n該類型下有 {len(notes_with_cat)} 條筆記，將移動到默認類型 '{self.default_category}'"
            else:
                msg += f"\n\n该类型下有 {len(notes_with_cat)} 条笔记，将移动到默认类型 '{self.default_category}'"

        if messagebox.askyesno("确认删除" if not self.is_trad else "確認刪除", msg):
            self.categories.remove(cat_to_delete)
            for note in self.notes:
                if note['category'] == cat_to_delete:
                    note['category'] = self.default_category
            self.save_data()
            self.refresh_category_list()
            self.update_category_lists()
            self.refresh_notes_list()
            delete_word = "已刪除類型" if self.is_trad else "已删除类型"
            self.update_status(f"{delete_word}: {cat_to_delete}")

    @log_memo_exceptions
    def set_default_category(self):
        """设置默认分类"""
        selection = self.cat_listbox.curselection()
        if not selection:
            if self.is_trad:
                messagebox.showwarning("提示", "請先選擇一個類型")
            else:
                messagebox.showwarning("提示", "请先选择一个类型")
            return

        new_default = self.categories[selection[0]]
        self.default_category = new_default
        self.save_data()
        self.refresh_category_list()
        self.update_status(f"默认类型已设置为: {new_default}")

    @log_memo_exceptions
    def update_category_lists(self):
        """更新主界面的分类控件选项"""
        if hasattr(self, 'filter_combo') and self.filter_combo:
            self.filter_combo['values'] = ["全部"] + self.categories
        if hasattr(self, 'category_combo') and self.category_combo:
            self.category_combo['values'] = self.categories

    @log_memo_exceptions
    def open_export_manager(self):
        """打开导出管理窗口"""
        if self.export_manager_window is not None and self.export_manager_window.winfo_exists():
            self.export_manager_window.lift()
            return

        self.export_manager_window = tk.Toplevel(self)
        self.export_manager_window.title("导出笔记" if not self.is_trad else "導出筆記")
        self.export_manager_window.geometry("900x750")
        self.export_manager_window.resizable(False, False)
        self.export_manager_window.transient(self)

        # 绑定关闭事件清理引用
        self.export_manager_window.protocol("WM_DELETE_WINDOW",
                                            lambda: (self.export_manager_window.destroy(),
                                                     setattr(self, 'export_manager_window', None)))

        path_frame = ttk.Frame(self.export_manager_window)
        path_frame.pack(fill=tk.X, padx=10, pady=10)

        dao_chu_label = ttk.Label(path_frame, text="導出路徑" if self.is_trad else "导出路径:", font=self.fonts['default'])
        dao_chu_label.pack(side=tk.LEFT)
        self.memo_register(dao_chu_label)

        # 路径显示框
        self.export_path_var = tk.StringVar(value=self.export_path)
        self.export_path_label = ttk.Entry(path_frame, textvariable=self.export_path_var,
                                           font=self.fonts['default'], state='readonly', width=35)
        self.export_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = tk.Button(path_frame, text="浏览..." if not self.is_trad else "瀏覽...",
                               command=self.browse_export_path,
                               font=self.fonts['default'], width=8)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(browse_btn)

        # 类型筛选
        filter_frame = ttk.Frame(self.export_manager_window)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        shai_xuan_label = ttk.Label(filter_frame, text="筛选类型:", font=self.fonts['default'])
        shai_xuan_label.pack(side=tk.LEFT)
        self.memo_register(shai_xuan_label)
        self.export_filter_var = tk.StringVar(value="全部")
        self.export_filter_combo = ttk.Combobox(filter_frame, textvariable=self.export_filter_var,
                                                values=["全部"] + self.categories,
                                                font=self.fonts['default'], state="readonly", width=15)
        self.export_filter_combo.pack(side=tk.LEFT, padx=10)

        # 全选按钮
        self.select_all_var = tk.BooleanVar(value=False)
        select_all_cb = ttk.Checkbutton(filter_frame, text="全选" if not self.is_trad else "全選",
                                        variable=self.select_all_var,
                                        command=self.toggle_select_all)
        select_all_cb.pack(side=tk.LEFT, padx=20)
        self.memo_register(select_all_cb)

        # 笔记列表
        list_frame = ttk.Frame(self.export_manager_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.export_listbox = tk.Listbox(list_frame, font=self.fonts['default'])
        self.export_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.export_listbox.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.export_listbox.config(yscrollcommand=y_scroll.set)

        # 绑定事件
        self.export_filter_combo.bind('<<ComboboxSelected>>',
                                      lambda e: self.refresh_export_list())
        self.export_listbox.bind('<Button-1>',
                                 lambda e: self.toggle_export_selection(e))

        # 初始化列表
        self.refresh_export_list()

        # 按钮区
        btn_frame = ttk.Frame(self.export_manager_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        confirm_btn = tk.Button(btn_frame, text="导出选中" if not self.is_trad else "導出選中",
                                command=self.execute_export,
                                font=self.fonts['default'], bg="#c9a6eb")
        confirm_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(confirm_btn)

        cancel_btn = tk.Button(btn_frame, text="取消" if not self.is_trad else "取消",
                               command=self.export_manager_window.destroy, font=self.fonts['default'])
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(cancel_btn)

    @log_memo_exceptions
    def refresh_export_list(self):
        """刷新导出列表并更新全选按钮状态"""
        self.export_listbox.delete(0, tk.END)

        filter_type = self.export_filter_var.get()
        if filter_type == "全部":
            notes_list = sorted(self.notes, key=lambda x: x['modified_time'], reverse=True)
        else:
            notes_list = sorted([n for n in self.notes if n['category'] == filter_type],
                                key=lambda x: x['modified_time'], reverse=True)

        # 检查当前显示列表是否全部已选中
        all_selected = len(notes_list) > 0
        for note in notes_list:
            if note['id'] not in self.export_selected_ids:
                all_selected = False
                break

        # 更新全选按钮状态
        if hasattr(self, 'select_all_var'):
            self.select_all_var.set(all_selected)

        for note in notes_list:
            prefix = "☑ " if note['id'] in self.export_selected_ids else "☐ "
            display_text = f"{prefix}{note['title'][:30]} | {note['category']} | {note['modified_time'][:10]}"
            self.export_listbox.insert(tk.END, display_text)

    @log_memo_exceptions
    def browse_export_path(self):
        """浏览选择导出文件夹"""
        path = filedialog.askdirectory(initialdir=self.export_path,
                                       title="选择导出文件夹" if not self.is_trad else "選擇導出文件夾")
        if path:
            self.export_path = path
            if hasattr(self, 'export_path_var'):
                self.export_path_var.set(path)
                self.save_data()  # 立即保存到配置文件

    @log_memo_exceptions
    def toggle_export_selection(self, event):
        """切换单个笔记的选择状态"""
        index = self.export_listbox.nearest(event.y)
        filter_type = self.export_filter_var.get()

        if filter_type == "全部":
            notes_list = sorted(self.notes, key=lambda x: x['modified_time'], reverse=True)
        else:
            notes_list = sorted([n for n in self.notes if n['category'] == filter_type],
                                key=lambda x: x['modified_time'], reverse=True)

        if 0 <= index < len(notes_list):
            note_id = notes_list[index]['id']
            if note_id in self.export_selected_ids:
                self.export_selected_ids.remove(note_id)
            else:
                self.export_selected_ids.add(note_id)

            # 重新检查全选状态
            all_selected = len(notes_list) > 0
            for note in notes_list:
                if note['id'] not in self.export_selected_ids:
                    all_selected = False
                    break
            self.select_all_var.set(all_selected)

            self.refresh_export_list()

    @log_memo_exceptions
    def toggle_select_all(self):
        """全选/取消全选当前显示的所有笔记"""
        filter_type = self.export_filter_var.get()
        if filter_type == "全部":
            notes_list = self.notes
        else:
            notes_list = [n for n in self.notes if n['category'] == filter_type]

        if self.select_all_var.get():
            for note in notes_list:
                self.export_selected_ids.add(note['id'])
        else:
            for note in notes_list:
                self.export_selected_ids.discard(note['id'])

        self.refresh_export_list()

    @log_memo_exceptions
    def execute_export(self):
        """执行导出，验证路径是否存在"""
        if not self.export_selected_ids:
            if self.is_trad:
                messagebox.showwarning("提示", "請選擇要導出的筆記")
            else:
                messagebox.showwarning("提示", "请选择要导出的笔记")
            return

        # 验证路径是否存在
        if not os.path.exists(self.export_path):
            msg = f"导出路径不存在:\n{self.export_path}\n\n请选择有效的路径。" if not self.is_trad else \
                f"導出路徑不存在:\n{self.export_path}\n\n請選擇有效的路徑。"
            messagebox.showwarning("路径错误" if not self.is_trad else "路徑錯誤", msg)
            return

        # 生成文件名（带时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.export_path, f"notes_export_{timestamp}.txt")

        notes_to_export = [n for n in self.notes if n['id'] in self.export_selected_ids]
        # notes_to_export.sort(key=lambda x: x['modified_time'], reverse=True)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for note in notes_to_export:
                    title = note['title']
                    content = note['content']
                    f.write(title)
                    f.write('\n\n')
                    f.write(content)
                    f.write("\n\n")

            self.update_status(f"已导出 {len(notes_to_export)} 条笔记到: {filename}")
            self.export_manager_window.destroy()
        except Exception as e:
            msg = f"导出失败:\n{str(e)}" if not self.is_trad else f"導出失敗:\n{str(e)}"
            messagebox.showerror("导出错误" if not self.is_trad else "導出錯誤", msg)

    @log_memo_exceptions
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        if hasattr(self, '_status_clear') and self._status_clear is not None:
            try:
                self.after_cancel(self._status_clear)
            except:
                pass

        self._status_clear = self.after(3000, lambda: self.status_var.set(""))

    @log_memo_exceptions
    def on_window_close(self):
        """窗口关闭时保存数据"""
        if not self.current_note_id:
            title = self.title_var.get().strip()
            content = self.content_text.get("1.0", tk.END).strip()
            if title or content:
                new_note = {
                    'id': str(datetime.now().timestamp()),
                    'title': title or "NoName",
                    'content': content,
                    'category': self.category_var.get().strip() or self.default_category,
                    'created_time': datetime.now().isoformat(),
                    'modified_time': datetime.now().isoformat()
                }
                self.notes.append(new_note)
        if hasattr(MemoInterface, '_instance'):
            MemoInterface._instance = None

        self.save_data()

        if self.winfo_exists():
            self.destroy()

        if hasattr(self.master, '_memo_window'):
            delattr(self.master, '_memo_window')