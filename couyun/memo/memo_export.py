import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox

from couyun.ui.core.logger_config import get_logger, log_exceptions
from couyun.memo.memo_common import update_status

logger = get_logger(__name__)

# noinspection PyTypeChecker
class ExportManager:
    """导出管理窗口"""
    def __init__(self, parent, notes, categories, export_path, fonts, is_trad):
        self.parent = parent
        self.categories = categories
        self.export_path = export_path
        self.fonts = fonts
        self.is_trad = is_trad
        self.notes = notes
        self.selected_ids = set()

        self.window = tk.Toplevel(parent)
        self._setup_window()
        self._create_ui()

    def _setup_window(self):
        self.window.title("导出笔记" if not self.is_trad else "導出筆記")
        self.window.geometry("900x750")
        self.window.resizable(False, False)
        self.window.transient(self.parent)

        # 关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self):
        # 路径显示框
        path_frame = ttk.Frame(self.window)
        path_frame.pack(fill=tk.X, padx=10, pady=10)

        dao_chu_label = ttk.Label(
            path_frame,
            text="導出路徑" if self.is_trad else "导出路径:",
            font=self.fonts['default']
        )
        dao_chu_label.pack(side=tk.LEFT)

        self.export_path_var = tk.StringVar(value=self.export_path)
        self.export_path_label = ttk.Entry(
            path_frame,
            textvariable=self.export_path_var,
            font=self.fonts['default'],
            state='readonly',
            width=35
        )
        self.export_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        browse_btn = tk.Button(
            path_frame,
            text="浏览..." if not self.is_trad else "瀏覽...",
            command=self.browse_export_path,
            font=self.fonts['default'],
            width=8
        )
        browse_btn.pack(side=tk.RIGHT, padx=5)


        # 类型筛选
        filter_frame = ttk.Frame(self.window)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        shai_xuan_label = ttk.Label(
            filter_frame,
            text="筛选类型:" if not self.is_trad else "篩選類型:",
            font=self.fonts['default']
        )
        shai_xuan_label.pack(side=tk.LEFT)

        self.export_filter_var = tk.StringVar(value="全部")
        self.export_filter_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.export_filter_var,
            values=["全部"] + self.categories,
            font=self.fonts['default'],
            state="readonly",
            width=15
        )
        self.export_filter_combo.pack(side=tk.LEFT, padx=10)

        self.select_all_var = tk.BooleanVar(value=False)
        select_all_cb = ttk.Checkbutton(
            filter_frame,
            text="全选" if not self.is_trad else "全選",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        select_all_cb.pack(side=tk.LEFT, padx=20)

        # 笔记列表
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.export_listbox = tk.Listbox(list_frame, font=self.fonts['default'])
        self.export_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.export_listbox.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.export_listbox.config(yscrollcommand=y_scroll.set)

        # 绑定事件
        self.export_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_export_list())
        self.export_listbox.bind('<Button-1>', lambda e: self.toggle_export_selection(e))

        # 初始化列表
        self.refresh_export_list()

        # 按钮区
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        confirm_btn = tk.Button(
            btn_frame,
            text="导出选中" if not self.is_trad else "導出選中",
            command=self.execute_export,
            font=self.fonts['default'],
            bg="#c9a6eb"
        )
        confirm_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = tk.Button(
            btn_frame,
            text="取消" if not self.is_trad else "取消",
            command=self.window.destroy,
            font=self.fonts['default']
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var, font=self.fonts['small'])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def browse_export_path(self):
        """浏览选择导出文件夹"""
        path = filedialog.askdirectory(initialdir=self.export_path,
                                       title="选择导出文件夹" if not self.is_trad else "選擇導出文件夾")
        if path:
            self.export_path = path
            if hasattr(self, 'export_path_var'):
                self.export_path_var.set(path)

    def toggle_select_all(self):
        """全选/取消全选当前显示的所有笔记"""
        filter_type = self.export_filter_var.get()
        if filter_type == "全部":
            notes_list = self.notes
        else:
            notes_list = [n for n in self.notes if n['category'] == filter_type]

        if self.select_all_var.get():
            for note in notes_list:
                self.selected_ids.add(note['id'])
        else:
            for note in notes_list:
                self.selected_ids.discard(note['id'])
        self.refresh_export_list()

    @log_exceptions
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
            if note['id'] not in self.selected_ids:
                all_selected = False
                break

        # 更新全选按钮状态
        if hasattr(self, 'select_all_var'):
            self.select_all_var.set(all_selected)

        for note in notes_list:
            prefix = "☑ " if note['id'] in self.selected_ids else "☐ "
            display_text = f"{prefix}{note['title'][:30]} | {note['category']} | {note['modified_time'][:10]}"
            self.export_listbox.insert(tk.END, display_text)

    @log_exceptions
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
            if note_id in self.selected_ids:
                self.selected_ids.remove(note_id)
            else:
                self.selected_ids.add(note_id)

            # 重新检查全选状态
            all_selected = len(notes_list) > 0
            for note in notes_list:
                if note['id'] not in self.selected_ids:
                    all_selected = False
                    break
            self.select_all_var.set(all_selected)

            self.refresh_export_list()

    @log_exceptions
    def execute_export(self):
        """执行导出，验证路径是否存在"""
        if not self.selected_ids:
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

        notes_to_export = [n for n in self.notes if n['id'] in self.selected_ids]
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

            self.window.destroy()
        except Exception as e:
            msg = f"导出失败:\n{str(e)}" if not self.is_trad else f"導出失敗:\n{str(e)}"
            messagebox.showerror("导出错误" if not self.is_trad else "導出錯誤", msg)

    def update_status(self, message):
        update_status(self, self.status_var, message)

    def _on_close(self):
        """关闭窗口时的清理操作"""
        self.window.destroy()
        # 可以在主程序里统一清理引用或刷新
