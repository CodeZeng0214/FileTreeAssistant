"""UI 界面模块 —— 基于 tkinter + ttkbootstrap 的主窗口"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from scanner import scan_directory, format_as_tree, get_statistics, FileNode
from exporter import export_txt, export_excel


class FileTreeApp:
    """文件目录树助手主应用"""

    def __init__(self):
        # 使用 ttkbootstrap 的淡蓝色主题
        self.root = ttkb.Window(
            themename="litera",  # 浅色主题，搭配淡蓝
            title="文件树助手",
            size=(960, 680),
            minsize=(700, 500),
        )
        
        # 当前扫描结果
        self.current_nodes: list[FileNode] = []
        self.current_root_path: str = ""
        self.tree_text: str = ""

        # 构建界面
        self._build_ui()
        
        # 居中窗口
        self._center_window()

    # =================================================================
    #  界面构建
    # =================================================================

    def _build_ui(self):
        """构建完整的 UI 布局"""
        # --- 样式定制 ---
        style = ttkb.Style()
        style.configure("TLabel", font=("微软雅黑", 10))
        style.configure("TButton", font=("微软雅黑", 10))
        style.configure("TCheckbutton", font=("微软雅黑", 10))
        style.configure("primary.TButton", font=("微软雅黑", 10, "bold"))
        
        # 主容器
        main_frame = ttkb.Frame(self.root, padding=(12, 10))
        main_frame.pack(fill=BOTH, expand=YES)

        # ---- 顶部操作栏 ----
        top_frame = ttkb.LabelFrame(main_frame, text="📂 扫描设置")
        top_frame.pack(fill=X, pady=(0, 8))
        top_inner = ttkb.Frame(top_frame, padding=(10, 8))
        top_inner.pack(fill=X)

        # 第1行：路径选择
        path_row = ttkb.Frame(top_inner)
        path_row.pack(fill=X, pady=(0, 6))

        ttkb.Label(path_row, text="目标文件夹：", width=12).pack(side=LEFT)
        
        self.path_var = tk.StringVar()
        path_entry = ttkb.Entry(path_row, textvariable=self.path_var, font=("微软雅黑", 10))
        path_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 6))
        
        browse_btn = ttkb.Button(
            path_row, text="浏览...", command=self._on_browse, 
            bootstyle="outline-primary", width=8
        )
        browse_btn.pack(side=LEFT)

        # 第2行：深度 + 扫描按钮
        ctrl_row = ttkb.Frame(top_inner)
        ctrl_row.pack(fill=X)

        depth_frame = ttkb.Frame(ctrl_row)
        depth_frame.pack(side=LEFT)

        ttkb.Label(depth_frame, text="扫描深度：").pack(side=LEFT, padx=(0, 4))
        
        self.depth_var = tk.StringVar(value="不限制")
        self.depth_combo = ttkb.Combobox(
            depth_frame, 
            textvariable=self.depth_var,
            values=["不限制", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            state="readonly",
            width=8,
            font=("微软雅黑", 10),
        )
        self.depth_combo.pack(side=LEFT, padx=(0, 4))
        ttkb.Label(depth_frame, text="级", font=("微软雅黑", 9)).pack(side=LEFT)

        # 扫描按钮
        self.scan_btn = ttkb.Button(
            ctrl_row, text="🔍 开始扫描", command=self._on_scan,
            bootstyle="primary", width=14
        )
        self.scan_btn.pack(side=RIGHT)

        # ---- 过滤面板 ----
        self.filter_frame = ttkb.LabelFrame(main_frame, text="🔽 过滤选项")
        self.filter_frame.pack(fill=X, pady=(0, 8))
        filter_inner = ttkb.Frame(self.filter_frame, padding=(10, 6))
        filter_inner.pack(fill=X)

        self.show_folders_var = tk.BooleanVar(value=True)
        self.show_files_var = tk.BooleanVar(value=True)

        cb_folder = ttkb.Checkbutton(
            filter_inner, text="显示文件夹", variable=self.show_folders_var,
            bootstyle="info-round-toggle"
        )
        cb_folder.pack(side=LEFT, padx=(0, 16))

        cb_file = ttkb.Checkbutton(
            filter_inner, text="显示文件", variable=self.show_files_var,
            bootstyle="info-round-toggle"
        )
        cb_file.pack(side=LEFT, padx=(0, 16))

        ttkb.Label(filter_inner, text="后缀筛选：").pack(side=LEFT, padx=(4, 4))
        
        self.ext_var = tk.StringVar()
        ext_entry = ttkb.Entry(
            filter_inner, textvariable=self.ext_var, 
            font=("微软雅黑", 10), width=22
        )
        ext_entry.pack(side=LEFT)
        ttkb.Label(
            filter_inner, 
            text="  例: .txt,.py  （留空=全部）",
            font=("微软雅黑", 8), foreground="#888"
        ).pack(side=LEFT)

        # 折叠按钮
        self.filter_visible = True
        self.toggle_filter_btn = ttkb.Button(
            self.filter_frame, text="收起 ▲", command=self._toggle_filter,
            bootstyle="link", width=8
        )
        # 按钮放在 label 旁边（通过 place 或重新组织）
        # 改为放在 main_frame 中的独立行更简洁 —— 在底部状态栏旁边

        # ---- 结果展示区 ----
        result_frame = ttkb.LabelFrame(main_frame, text="📋 扫描结果")
        result_inner = ttkb.Frame(result_frame, padding=(8, 6))
        result_inner.pack(fill=BOTH, expand=YES)
        result_frame.pack(fill=BOTH, expand=YES, pady=(0, 8))

        # 树形文本显示（等宽字体）
        self.result_text = tk.Text(
            result_inner,
            font=("Consolas", 10),
            wrap=tk.NONE,
            bg="#FAFAFA",
            fg="#263238",
            relief=tk.FLAT,
            padx=8,
            pady=6,
            selectbackground="#90CAF9",
            selectforeground="#0D47A1",
        )
        self.result_text.pack(fill=BOTH, expand=YES)

        # 滚动条
        v_scroll = ttkb.Scrollbar(result_inner, orient=VERTICAL, command=self.result_text.yview)
        v_scroll.pack(side=RIGHT, fill=Y)
        h_scroll = ttkb.Scrollbar(result_inner, orient=HORIZONTAL, command=self.result_text.xview)
        h_scroll.pack(side=BOTTOM, fill=X)
        self.result_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        # ---- 底部操作栏 ----
        bottom_frame = ttkb.Frame(main_frame)
        bottom_frame.pack(fill=X)

        self.status_label = ttkb.Label(
            bottom_frame, 
            text="就绪 — 请选择文件夹后点击「开始扫描」",
            font=("微软雅黑", 9), foreground="#666"
        )
        self.status_label.pack(side=LEFT, padx=(2, 0))

        btn_frame = ttkb.Frame(bottom_frame)
        btn_frame.pack(side=RIGHT)

        self.copy_btn = ttkb.Button(
            btn_frame, text="📋 复制到剪贴板", command=self._on_copy,
            bootstyle="outline-secondary", width=18
        )
        self.copy_btn.pack(side=LEFT, padx=(0, 6))

        self.export_txt_btn = ttkb.Button(
            btn_frame, text="📄 导出 TXT", command=self._on_export_txt,
            bootstyle="outline-secondary", width=14
        )
        self.export_txt_btn.pack(side=LEFT, padx=(0, 6))

        self.export_excel_btn = ttkb.Button(
            btn_frame, text="📊 导出 Excel", command=self._on_export_excel,
            bootstyle="outline-secondary", width=16
        )
        self.export_excel_btn.pack(side=LEFT)

        # 初始禁用导出按钮
        self._set_export_buttons_state(False)

    # =================================================================
    #  事件处理
    # =================================================================

    def _on_browse(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要扫描的文件夹", parent=self.root)
        if folder:
            self.path_var.set(folder)

    def _on_scan(self):
        """执行扫描"""
        root_path = self.path_var.get().strip()
        if not root_path:
            messagebox.showwarning("提示", "请先选择要扫描的文件夹。", parent=self.root)
            return
        if not os.path.isdir(root_path):
            messagebox.showerror("错误", "文件夹路径无效，请重新选择。", parent=self.root)
            return

        # 解析深度
        depth_str = self.depth_var.get().strip()
        max_depth = None if depth_str == "不限制" else int(depth_str)

        # 解析后缀
        ext_str = self.ext_var.get().strip()
        extensions = None
        if ext_str:
            extensions = [e.strip() for e in ext_str.split(",") if e.strip()]

        # 过滤选项
        show_folders = self.show_folders_var.get()
        show_files = self.show_files_var.get()

        if not show_folders and not show_files:
            messagebox.showwarning("提示", "请至少勾选「显示文件夹」或「显示文件」。", parent=self.root)
            return

        # 执行扫描
        try:
            self.scan_btn.configure(text="⏳ 扫描中...", state="disabled")
            self.root.update()

            nodes = scan_directory(
                root_path,
                max_depth=max_depth,
                show_folders=show_folders,
                show_files=show_files,
                extensions=extensions,
            )
            self.current_nodes = nodes
            self.current_root_path = root_path

            # 格式化树形文本
            self.tree_text = format_as_tree(nodes, root_path)
            if not self.tree_text.strip():
                self.tree_text = "(该文件夹下没有匹配的内容)"

            # 显示结果
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", self.tree_text)

            # 统计信息
            stats = get_statistics(nodes)
            status = (
                f"扫描完成 — 📁 {stats['dir_count']} 个文件夹 | "
                f"📄 {stats['file_count']} 个文件 | "
                f"💾 总大小 {stats['total_size_str']}"
            )
            self.status_label.configure(text=status)
            self._set_export_buttons_state(True)

        except Exception as e:
            messagebox.showerror("扫描出错", f"扫描过程中发生错误：\n{e}", parent=self.root)
            self.status_label.configure(text="扫描失败")
        finally:
            self.scan_btn.configure(text="🔍 开始扫描", state="normal")

    def _on_copy(self):
        """复制树形文本到剪贴板"""
        if not self.tree_text:
            return
        try:
            import pyperclip
            pyperclip.copy(self.tree_text)
            self.status_label.configure(text="✅ 已复制到剪贴板！")
            self.root.after(3000, lambda: self.status_label.configure(
                text=self.status_label.cget("text").replace("✅ 已复制到剪贴板！", 
                    f"扫描完成（已复制）")
            ))
        except Exception as e:
            messagebox.showerror("复制失败", f"复制到剪贴板时出错：\n{e}", parent=self.root)

    def _on_export_txt(self):
        """导出 TXT"""
        if not self.current_nodes:
            return
        success = export_txt(self.current_nodes, self.current_root_path, parent_window=self.root)
        if success:
            self.status_label.configure(text="✅ TXT 导出成功！")

    def _on_export_excel(self):
        """导出 Excel（先询问格式）"""
        if not self.current_nodes:
            return
        
        # 弹窗选择导出格式
        choice = messagebox.askyesnocancel(
            "Excel 导出格式",
            "请选择导出格式：\n\n"
            "  · 「是」— 完整信息（层级、名称、类型、大小、修改日期、路径）\n"
            "  · 「否」— 基础信息（层级、名称、类型、路径）\n"
            "  · 「取消」— 不导出",
            parent=self.root,
        )
        if choice is None:
            return  # 取消

        success = export_excel(
            self.current_nodes, self.current_root_path, 
            full_info=choice, parent_window=self.root
        )
        if success:
            self.status_label.configure(text="✅ Excel 导出成功！")

    def _toggle_filter(self):
        """折叠/展开过滤面板"""
        self.filter_visible = not self.filter_visible
        if self.filter_visible:
            self.toggle_filter_btn.configure(text="收起 ▲")
            # 显示过滤内容
            for child in self.filter_frame.winfo_children():
                if child != self.toggle_filter_btn:
                    child.pack()
        else:
            self.toggle_filter_btn.configure(text="展开 ▼")
            for child in self.filter_frame.winfo_children():
                if child != self.toggle_filter_btn:
                    child.pack_forget()

    def _set_export_buttons_state(self, enabled: bool):
        """启用/禁用导出按钮"""
        state = "normal" if enabled else "disabled"
        self.copy_btn.configure(state=state)
        self.export_txt_btn.configure(state=state)
        self.export_excel_btn.configure(state=state)

    def _center_window(self):
        """窗口居中"""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def run(self):
        """启动应用"""
        self.root.mainloop()
