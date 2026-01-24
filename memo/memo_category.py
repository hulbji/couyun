import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import copy

from couyun.ui.core.logger_config import get_logger, log_exceptions
from couyun.memo.memo_common import update_status

logger = get_logger(__name__)

# noinspection PyTypeChecker
class CategoryManager:
    def __init__(self, parent, notes, categories, default_category, fonts, is_trad):
        self.parent = parent
        self.notes = copy.deepcopy(notes)
        self.categories = categories.copy()
        self.default_category = default_category
        self.fonts = fonts
        self.is_trad = is_trad

        self.window = tk.Toplevel(parent)
        self._setup_window()
        self._create_ui()
        self.dirty = False

    def _setup_window(self):
        self.window.title("管理类型" if not self.is_trad else "管理類型")
        self.window.geometry("800x500")
        self.window.resizable(False, False)
        self.window.transient(self.parent)

    def _create_ui(self):
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.cat_listbox = tk.Listbox(list_frame, font=self.fonts['default'], selectmode=tk.SINGLE)
        self.cat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.refresh_category_list()

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.cat_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cat_listbox.config(yscrollcommand=scrollbar.set)

        # 按钮框架
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        self._create_buttons(btn_frame)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.window, textvariable=self.status_var, font=self.fonts['small'])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_buttons(self, parent):
        """创建所有按钮"""
        btn_configs = [
            ("新建类型" if not self.is_trad else "新建類型", self.add_category, 12),
            ("重命名" if not self.is_trad else "重命名", self.rename_category, 9),
            ("删除" if not self.is_trad else "刪除", self.delete_category, 6),
            ("设为默认" if not self.is_trad else "設為默認", self.set_default_category, 12),
            ("关闭" if not self.is_trad else "關閉", self.window.destroy, 6)
        ]

        for text, command, width in btn_configs:
            btn = tk.Button(parent, text=text, command=command,
                            font=self.fonts['default'], width=width)
            if command == self.window.destroy:  # 关闭按钮放右边
                btn.pack(side=tk.RIGHT, padx=5)
            else:
                btn.pack(side=tk.LEFT, padx=5)

    @log_exceptions
    def refresh_category_list(self):
        """刷新分类列表显示"""
        self.cat_listbox.delete(0, tk.END)
        for cat in self.categories:
            display = cat
            if cat == self.default_category:
                display += " (默认)" if not self.is_trad else " (默認)"
            self.cat_listbox.insert(tk.END, display)
        self.dirty = True

    @log_exceptions
    def add_category(self):
        """添加新分类"""
        new_cat = simpledialog.askstring("新建类型" if not self.is_trad else "新建類型",
                                         "请输入新类型名称:" if not self.is_trad else "請輸入新類型名稱:")
        if new_cat and new_cat.strip():
            new_cat = new_cat.strip()
            if new_cat not in self.categories:
                self.categories.append(new_cat)
                # self.save_data()
                self.refresh_category_list()
                self.update_category_lists()
                self.update_status(f"已添加类型: {new_cat}" if not self.is_trad else f"已添加類型: {new_cat}")
            else:
                if self.is_trad:
                    messagebox.showwarning("提示", "該類型已存在")
                else:
                    messagebox.showwarning("提示", "该类型已存在")

    @log_exceptions
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
            # self.save_data()
            self.refresh_category_list()
            self.update_category_lists()
            self.update_status(f"已重命名: {old_cat} -> {new_cat}")

    @log_exceptions
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
            # self.save_data()
            self.refresh_category_list()
            self.update_category_lists()
            delete_word = "已刪除類型" if self.is_trad else "已删除类型"
            self.update_status(f"{delete_word}: {cat_to_delete}")

    @log_exceptions
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
        # self.save_data()
        self.refresh_category_list()
        self.update_status(f"默认类型已设置为: {new_default}")

    @log_exceptions
    def update_category_lists(self):
        """更新主界面的分类控件选项"""
        if hasattr(self, 'filter_combo') and self.filter_combo:
            self.filter_combo['values'] = ["全部"] + self.categories
        if hasattr(self, 'category_combo') and self.category_combo:
            self.category_combo['values'] = self.categories
        self.dirty = True

    def update_status(self, message):
        update_status(self, self.status_var, message)
