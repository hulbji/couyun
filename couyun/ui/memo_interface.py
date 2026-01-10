import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from couyun.ui.core.logger_config import get_logger, log_exceptions
from couyun.memo.memo_common import update_status
from couyun.memo.memo_category import CategoryManager
from couyun.memo.memo_export import ExportManager

logger = get_logger(__name__)

# noinspection PyTypeChecker
class MemoInterface(tk.Toplevel):
    def __init__(self, parent, fonts, resource_path, is_trad):

        self.widgets_to_translate = []
        self.s2t = str.maketrans("个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
                                 "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验",
                                 "个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
                                 "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗")
        self.t2s = str.maketrans("个爲從體關內擊創動區單雙變後嗎圖處備夾導將帶並開當錄徑態執擇換據數舊時顯條來標欄檢橫"
                                 "瀏滾點狀畱稱筆篩簡類組綁編獲視覽認記設證詞譯詩該詳誤請讀調敗轉載輯輸這進選鈕錯閉間頁項題驗",
                                 "个为从体关内击创动区单双变后吗图处备夹导将带并开当录径态执择换据数旧时显条来标栏检横"
                                 "浏滚点状留称笔筛简类组绑编获视览认记设证词译诗该详误请读调败转载辑输这进选钮错闭间页项题验")
        super().__init__(parent.root)

        self.fonts = fonts
        self.resource_path = resource_path
        self.is_trad = is_trad
        self.parent = parent

        self.data_path = os.path.join(os.path.dirname(resource_path()), './assets/state/memo_data.json')

        self.title("備忘錄" if is_trad else "备忘录")
        self.geometry("1000x800")
        self.resizable(False, False)

        self.notes = []
        self.categories = ["诗词", "摘抄"]
        self.default_category = "诗词"
        self.current_filter = "全部"
        self.search_keyword = ""
        self.sort_mode = "时间倒序"
        self.current_displayed_notes = []

        self.selected_ids = set()
        self.export_path = os.getcwd()
        self.validate_choice_window = None

        self.current_note_id = None
        self.status_var = None
        self.toggle_btn = None
        self.content_text = None
        self.category_var = None
        self.title_var = None
        self.detail_frame = None
        self.notes_listbox = None
        self.sort_var = None
        self.filter_var = None
        self.search_var = None
        self.main_frame = None

        self.load_data()
        self.create_ui()
        self.show_list_view()
        self.after_idle(self._post_ui_init)

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)

    @ log_exceptions
    def _post_ui_init(self):
        """
        UI 已经显示后，再执行的慢操作
        """
        self.refresh_notes_list()
        self.update_status("")

    def memo_register(self, widget):
        """注册需要翻译的控件"""
        self.widgets_to_translate.append(widget)

    @log_exceptions
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

    @log_exceptions
    def cc_convert(self, text, to_trad: bool):
        """根据目标模式转换文本"""
        return text.translate(self.s2t) if to_trad else text.translate(self.t2s)

    @log_exceptions
    def create_ui(self):
        """UI 总入口，只负责调度"""
        self.create_main_ui()
        self.create_detail_ui()
        self.create_status_bar()

        self.show_list_view()

    @log_exceptions
    def create_main_ui(self):
        """备忘录主界面"""
        self.main_frame = ttk.Frame(self)

        # ===== 搜索区 =====
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=8)

        search_label = ttk.Label(
            search_frame,
            text="搜索",
            font=self.fonts['default']
        )
        search_label.pack(side=tk.LEFT)
        self.memo_register(search_label)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=self.fonts['default']
        )
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        search_entry.bind('<KeyRelease>', self.on_search)

        # ===== 筛选 / 排序区 =====
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 8))

        type_label = ttk.Label(
            control_frame,
            text="类型:" if not self.is_trad else "類型:",
            font=self.fonts['default']
        )
        type_label.pack(side=tk.LEFT)
        self.memo_register(type_label)

        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(
            control_frame,
            textvariable=self.filter_var,
            values=["全部"] + self.categories,
            font=self.fonts['default'],
            state="readonly",
            width=12
        )
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', self.on_filter_change)

        sort_label = ttk.Label(
            control_frame,
            text="排序",
            font=self.fonts['default']
        )
        sort_label.pack(side=tk.LEFT, padx=(20, 5))
        self.memo_register(sort_label)

        self.sort_var = tk.StringVar(value=self.sort_mode)
        sort_combo = ttk.Combobox(
            control_frame,
            textvariable=self.sort_var,
            values=(
                ["时间倒序", "时间正序", "标题", "类型"]
                if not self.is_trad else
                ["時間倒序", "時間正序", "標題", "類型"]
            ),
            font=self.fonts['default'],
            state="readonly",
            width=12
        )
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_change)
        self.memo_register(sort_combo)

        # ===== 列表区（唯一 expand）=====
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.notes_listbox = tk.Listbox(
            list_frame,
            font=self.fonts['default']
        )
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(list_frame, command=self.notes_listbox.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.notes_listbox.config(yscrollcommand=y_scroll.set)

        self.notes_listbox.bind('<Double-1>', self.on_note_select)
        self.notes_listbox.bind(
            '<<ListboxSelect>>',
            lambda e: self.after_idle(self.on_note_select)
        )

        self.notes_listbox.bind('<Button-1>', self.on_listbox_click)

        # ===== 底部按钮区（固定）=====
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, pady=8)

        new_btn_main = tk.Button(
            btn_frame,
            text="+ 新建笔记" if not self.is_trad else "+ 新建筆記",
            command=self.show_new_note_view,
            font=self.fonts['default'],
            bg="#c9a6eb",
            width=12
        )
        new_btn_main.pack(side=tk.LEFT, padx=5)
        self.memo_register(new_btn_main)

        manage_cat_btn = tk.Button(
            btn_frame,
            text="管理类型" if not self.is_trad else "管理類型",
            command=self.open_category_manager,
            font=self.fonts['default'],
            width=12
        )
        manage_cat_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(manage_cat_btn)

        export_btn = tk.Button(
            btn_frame,
            text="导出笔记" if not self.is_trad else "導出筆記",
            command=self.open_export_manager,
            font=self.fonts['default'],
            width=12
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(export_btn)

        self.toggle_btn = tk.Button(
            btn_frame,
            text="繁體" if not self.is_trad else "简体",
            command=self.toggle_language,
            font=self.fonts['default'],
            width=12
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(self.toggle_btn)

        close_btn = tk.Button(
            btn_frame,
            text="关闭" if not self.is_trad else "關閉",
            command=self.destroy,
            font=self.fonts['default'],
            width=12
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(close_btn)

    @log_exceptions
    def create_detail_ui(self):
        """笔记详情 / 编辑界面"""

        self.detail_frame = ttk.Frame(self)

        # ===== 顶部（固定）=====
        title_frame = ttk.Frame(self.detail_frame)
        title_frame.pack(fill=tk.X, pady=8)

        title_label = ttk.Label(
            title_frame,
            text="标题:" if not self.is_trad else "標題:",
            font=self.fonts['bigger']
        )
        title_label.pack(side=tk.LEFT)
        self.memo_register(title_label)

        self.title_var = tk.StringVar()
        title_entry = ttk.Entry(
            title_frame,
            textvariable=self.title_var,
            font=self.fonts['bigger']
        )
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        category_label = ttk.Label(
            title_frame,
            text="类型:" if not self.is_trad else "類型:",
            font=self.fonts['default']
        )
        category_label.pack(side=tk.LEFT)
        self.memo_register(category_label)

        self.category_var = tk.StringVar()
        category_combo = ttk.Combobox(
            title_frame,
            textvariable=self.category_var,
            values=self.categories,
            font=self.fonts['default'],
            width=15
        )
        category_combo.pack(side=tk.LEFT, padx=5)

        # ===== 中部（唯一 expand，关键修复点）=====
        content_container = ttk.Frame(self.detail_frame)
        content_container.pack(fill=tk.BOTH, expand=True)

        # 🔴 关键：禁止 Text 决定父容器最小高度
        content_container.pack_propagate(False)

        self.content_text = tk.Text(
            content_container,
            font=self.fonts['default'],
            wrap=tk.WORD
        )
        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content_scroll = ttk.Scrollbar(
            content_container,
            orient=tk.VERTICAL,
            command=self.content_text.yview
        )
        content_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.content_text.config(yscrollcommand=content_scroll.set)

        # ===== 底部按钮区（固定，永远可见）=====
        detail_btn_frame = ttk.Frame(self.detail_frame)
        detail_btn_frame.pack(fill=tk.X, pady=8)

        save_btn = tk.Button(
            detail_btn_frame,
            text="💾 保存" if not self.is_trad else "💾 儲存",
            command=self.save_current_note,
            font=self.fonts['default'],
            bg="#c9a6eb",
            width=12
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(save_btn)

        validate_btn = tk.Button(
            detail_btn_frame,
            text="🔍 校验" if not self.is_trad else "🔍 校驗",
            command=self.open_validate_choice,
            font=self.fonts['default'],
            width=12
        )
        validate_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(validate_btn)

        delete_btn = tk.Button(
            detail_btn_frame,
            text="🗑️ 删除" if not self.is_trad else "🗑️ 刪除",
            command=self.delete_note,
            font=self.fonts['default'],
            width=12
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        self.memo_register(delete_btn)

        return_btn = tk.Button(
            detail_btn_frame,
            text="← 返回列表" if not self.is_trad else "← 返回清單",
            command=self.show_list_view,
            font=self.fonts['default'],
            width=12
        )
        return_btn.pack(side=tk.RIGHT, padx=5)
        self.memo_register(return_btn)

    @log_exceptions
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            self,
            textvariable=self.status_var,
            font=self.fonts['small']
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    @log_exceptions
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
        self.parent.validate_content(mode, content)
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
            self.save_data()

    @log_exceptions
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

    @log_exceptions
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

    @log_exceptions
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

    @log_exceptions
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

    @log_exceptions
    def on_search(self, _):
        """搜索事件"""
        self.search_keyword = self.search_var.get().strip().lower()
        self.refresh_notes_list()

    @log_exceptions
    def on_filter_change(self, _):
        """筛选变化事件"""
        self.current_filter = self.filter_var.get()
        self.refresh_notes_list()

    @log_exceptions
    def on_sort_change(self, _):
        """排序变化事件"""
        self.sort_mode = self.sort_var.get()
        self.refresh_notes_list()

    @log_exceptions
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

    @log_exceptions
    def get_filtered_notes(self):
        """获取筛选后的笔记"""
        filtered = self.notes
        if self.search_keyword:
            filtered = [n for n in filtered if self.search_keyword in n['title'].lower() or
                        self.search_keyword in n['content'].lower()]
        if self.current_filter != "全部":
            filtered = [n for n in filtered if n['category'] == self.current_filter]
        return filtered

    @log_exceptions
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

    @log_exceptions
    def refresh_notes_list(self):
        """刷新笔记列表显示"""
        self.notes_listbox.delete(0, tk.END)
        notes = self.get_filtered_notes()
        notes = self.sort_notes(notes)

        self.current_displayed_notes = notes

        for note in notes:
            display_text = f"{note['title'][:35]} | {note['category']} | {note['modified_time'][:10]}"
            self.notes_listbox.insert(tk.END, display_text)

    @log_exceptions
    def open_category_manager(self):
        """打开分类管理窗口（模态），关闭后统一刷新主界面"""

        mgr = CategoryManager(
            parent=self,
            notes=self.notes,
            categories=self.categories,
            default_category=self.default_category,
            fonts=self.fonts,
            is_trad=self.is_trad
        )
        # mgr.window.transient(self)
        mgr.window.grab_set()
        self.wait_window(mgr.window)

        if mgr.dirty:
            self.default_category = mgr.default_category
            self.categories = mgr.categories
            self.notes = mgr.notes

            self.refresh_notes_list()
            self.save_data()

            self.update_status("分类已更新" if not self.is_trad else "類型已更新")

    @log_exceptions
    def open_export_manager(self):
        """打开导出管理窗口（模态），关闭后统一处理"""

        mgr = ExportManager(
            parent=self,
            notes=self.notes,
            categories=self.categories,
            export_path=self.export_path,
            fonts=self.fonts,
            is_trad=self.is_trad
        )

        mgr.window.grab_set()
        self.wait_window(mgr.window)
        self.update_status(f"已导出笔记到: {self.export_path}")
        self.export_path = mgr.export_path

    def update_status(self, message):
        update_status(self, self.status_var, message)

    @log_exceptions
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