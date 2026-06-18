"""UI 界面模块 —— 基于 tkinter + ttkbootstrap 的主窗口，支持文件夹拖入"""

import ctypes
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

from tkinterdnd2 import TkinterDnD, DND_FILES

from scanner import scan_directory, format_as_tree, get_statistics, FileNode
from exporter import export_txt, export_excel


def _enable_windows_dpi_awareness():
    """启用 Windows 高 DPI 感知（避免界面模糊），对标 ttkbootstrap.Window 的行为"""
    if os.name != "nt":
        return
    try:
        # 优先尝试 Per-Monitor V2（Windows 10 1703+），可获得最清晰的缩放效果
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # 回退到系统级 DPI 感知
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                # 最后的兜底方案
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


class FileTreeApp:
    """文件目录树助手主应用"""

    def __init__(self):
        # 启用高 DPI 感知 —— 必须在创建任何 tk 窗口之前调用
        _enable_windows_dpi_awareness()

        # 使用 TkinterDnD.Tk 作为根窗口（支持拖放），手动应用 ttkbootstrap 主题
        self.root = TkinterDnD.Tk()
        self.root.title("文件树助手")
        self.root.geometry("960x680")
        self.root.minsize(960, 600)
        
        # 根据屏幕 DPI 调整 tk 缩放比例
        self._apply_tk_dpi_scaling()

        # 应用 ttkbootstrap 主题（litera 浅色主题 + 淡蓝风格）
        self._style = ttkb.Style("litera")
        
        # 当前扫描结果
        self.current_nodes: list[FileNode] = []
        self.current_root_path: str = ""
        self.tree_text: str = ""

        # 构建界面
        self._build_ui()
        
        # 注册拖放支持
        self._setup_drag_drop()
        
        # 居中窗口
        self._center_window()

    # =================================================================
    #  界面构建
    # =================================================================

    def _build_ui(self):
        """构建完整的 UI 布局"""
        # --- 样式定制（统一放大字号） ---
        style = ttkb.Style()
        style.configure("TLabel", font=("微软雅黑", 12))
        style.configure("TButton", font=("微软雅黑", 12))
        style.configure("TCheckbutton", font=("微软雅黑", 12))
        style.configure("primary.TButton", font=("微软雅黑", 12, "bold"))
        
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
        self.path_entry = ttkb.Entry(path_row, textvariable=self.path_var, font=("微软雅黑", 12))
        self.path_entry.pack(side=LEFT, fill=X, expand=YES, padx=(0, 6))
        
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
            font=("微软雅黑", 12),
        )
        self.depth_combo.pack(side=LEFT, padx=(0, 4))
        ttkb.Label(depth_frame, text="级", font=("微软雅黑", 11)).pack(side=LEFT)

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
            font=("微软雅黑", 12), width=22
        )
        ext_entry.pack(side=LEFT)
        ttkb.Label(
            filter_inner, 
            text="  例: .txt,.py  （留空=全部）",
            font=("微软雅黑", 10), foreground="#888"
        ).pack(side=LEFT)

        # 折叠按钮
        self.filter_visible = True
        self.toggle_filter_btn = ttkb.Button(
            self.filter_frame, text="收起 ▲", command=self._toggle_filter,
            bootstyle="link", width=8
        )
        # 按钮放在 label 旁边（通过 place 或重新组织）
        # 改为放在 main_frame 中的独立行更简洁 —— 在底部状态栏旁边

        # ---- 底部操作栏（两行：状态行 + 按钮行） ----
        bottom_frame = ttkb.Frame(main_frame)
        bottom_frame.pack(fill=X, side=BOTTOM, pady=(8, 0))

        # 第1行：状态信息
        status_row = ttkb.Frame(bottom_frame)
        status_row.pack(fill=X, side=TOP)
        self.status_label = ttkb.Label(
            status_row, 
            text="就绪 — 请选择文件夹后点击「开始扫描」",
            font=("微软雅黑", 11), foreground="#666",
        )
        self.status_label.pack(side=LEFT, padx=(2, 0))

        # 第2行：操作按钮（右对齐）
        btn_row = ttkb.Frame(bottom_frame)
        btn_row.pack(fill=X, side=TOP, pady=(2, 0))
        btn_frame = ttkb.Frame(btn_row)
        btn_frame.pack(side=RIGHT)

        self.copy_btn = ttkb.Button(
            btn_frame, text="📋 复制到剪贴板", command=self._on_copy,
            bootstyle="outline-secondary", width=16
        )
        self.copy_btn.pack(side=LEFT, padx=(0, 4))

        self.export_txt_btn = ttkb.Button(
            btn_frame, text="📄 导出 TXT", command=self._on_export_txt,
            bootstyle="outline-secondary", width=12
        )
        self.export_txt_btn.pack(side=LEFT, padx=(0, 4))

        self.export_excel_btn = ttkb.Button(
            btn_frame, text="📊 导出 Excel", command=self._on_export_excel,
            bootstyle="outline-secondary", width=14
        )
        self.export_excel_btn.pack(side=LEFT)

        # 初始禁用导出按钮
        self._set_export_buttons_state(False)

        # ---- 结果展示区（最后 pack，占据剩余空间） ----
        result_frame = ttkb.LabelFrame(main_frame, text="📋 扫描结果")
        result_frame.pack(fill=BOTH, expand=YES, pady=(0, 0))
        result_inner = ttkb.Frame(result_frame, padding=(8, 6))
        result_inner.pack(fill=BOTH, expand=YES)

        # 树形文本显示（等宽字体）
        # 嵌套布局：先 pack 横向滚动条占位（底部），再 text_frame（剩余空间）
        h_scroll = ttkb.Scrollbar(result_inner, orient=HORIZONTAL)
        h_scroll.pack(side=BOTTOM, fill=X)

        text_frame = ttkb.Frame(result_inner)
        text_frame.pack(fill=BOTH, expand=YES)

        self.result_text = tk.Text(
            text_frame,
            font=("Consolas", 11),
            wrap=tk.NONE,
            bg="#FAFAFA",
            fg="#263238",
            relief=tk.FLAT,
            padx=8,
            pady=6,
            selectbackground="#90CAF9",
            selectforeground="#0D47A1",
        )
        self.result_text.pack(side=LEFT, fill=BOTH, expand=YES)

        # 垂直滚动条（右侧）
        v_scroll = ttkb.Scrollbar(text_frame, orient=VERTICAL, command=self.result_text.yview)
        v_scroll.pack(side=RIGHT, fill=Y)

        # 绑定横向滚动条（延迟绑定，因为需要 self.result_text 先存在）
        h_scroll.configure(command=self.result_text.xview)
        self.result_text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    # =================================================================
    #  事件处理
    # =================================================================

    def _on_browse(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择要扫描的文件夹", parent=self.root)
        if folder:
            self.path_var.set(folder)

    # =================================================================
    #  拖放支持
    # =================================================================

    def _setup_drag_drop(self):
        """注册拖放目标（根窗口 + 路径输入框）"""
        # 根窗口作为拖放目标
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._on_drop)
        self.root.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.root.dnd_bind("<<DropLeave>>", self._on_drop_leave)

        # 路径输入框也作为拖放目标（体验更好）
        self.path_entry.drop_target_register(DND_FILES)
        self.path_entry.dnd_bind("<<Drop>>", self._on_drop)
        self.path_entry.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.path_entry.dnd_bind("<<DropLeave>>", self._on_drop_leave)

    def _on_drop_enter(self, event):
        """拖入时高亮提示"""
        self.path_entry.configure(foreground="#1565C0")
        self.path_var.set("📂 释放鼠标以选择此文件夹...")

    def _on_drop_leave(self, event):
        """拖离时恢复原状"""
        self.path_entry.configure(foreground="")
        if not self.current_root_path:
            self.path_var.set("")

    def _on_drop(self, event):
        """处理文件夹拖入事件"""
        raw_data = event.data
        # 清理路径（去除花括号和换行等）
        path = raw_data.strip().strip("{}").strip()
        
        # Windows 可能返回用空格分隔的多个路径，取第一个
        if path:
            # 处理可能的多文件拖入（仅取第一个）
            paths = path.split("} {")
            if len(paths) > 1:
                path = paths[0].strip("{}")
            
            # 验证路径
            if os.path.isdir(path):
                self.path_var.set(path)
                # 可选：自动触发扫描
                # self._on_scan()
            elif os.path.isfile(path):
                # 如果是文件，取其所在文件夹
                parent_dir = os.path.dirname(path)
                self.path_var.set(parent_dir)
            else:
                messagebox.showwarning("提示", f"无法识别的路径：\n{path}", parent=self.root)
                self.path_var.set("")
        
        self.path_entry.configure(foreground="")

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

            # 统计信息（精简格式，避免挤走按钮）
            stats = get_statistics(nodes)
            status = (
                f"📁 {stats['dir_count']} 文件夹  "
                f"📄 {stats['file_count']} 文件  "
                f"💾 {stats['total_size_str']}"
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
            prev_text = self.status_label.cget("text")
            self.status_label.configure(text="✅ 已复制到剪贴板！")
            self.root.after(3000, lambda: self.status_label.configure(text=prev_text))
        except Exception as e:
            messagebox.showerror("复制失败", f"复制到剪贴板时出错：\n{e}", parent=self.root)

    def _on_export_txt(self):
        """导出 TXT"""
        if not self.current_nodes:
            messagebox.showwarning("提示", "请先扫描一个文件夹。", parent=self.root)
            return
        try:
            success = export_txt(self.current_nodes, self.current_root_path, parent_window=self.root)
            if success:
                self.status_label.configure(text="✅ TXT 导出成功！")
            else:
                self.status_label.configure(text="已取消 TXT 导出")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出 TXT 时出错：\n{e}", parent=self.root)

    def _on_export_excel(self):
        """导出 Excel（先询问格式）"""
        if not self.current_nodes:
            messagebox.showwarning("提示", "请先扫描一个文件夹。", parent=self.root)
            return
        
        # 弹窗选择导出格式
        choice = messagebox.askyesnocancel(
            "Excel 导出格式",
            "请选择导出格式：\n\n"
            "  · 「是(Y)」— 完整信息（层级、名称、类型、大小、修改日期、路径）\n"
            "  · 「否(N)」— 基础信息（层级、名称、类型、路径）\n"
            "  · 「取消」— 不导出",
            parent=self.root,
        )
        if choice is None:
            self.status_label.configure(text="已取消 Excel 导出")
            return

        try:
            success = export_excel(
                self.current_nodes, self.current_root_path, 
                full_info=choice, parent_window=self.root
            )
            if success:
                self.status_label.configure(text="✅ Excel 导出成功！")
            else:
                self.status_label.configure(text="已取消 Excel 导出")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出 Excel 时出错：\n{e}", parent=self.root)

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

    def _apply_tk_dpi_scaling(self):
        """根据屏幕 DPI 设置 tk 内部缩放比例，确保高 DPI 下字体清晰"""
        if os.name != "nt":
            return
        try:
            # 获取系统 DPI
            hdc = ctypes.windll.user32.GetDC(0)
            dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
            ctypes.windll.user32.ReleaseDC(0, hdc)
            # 标准 DPI = 96，计算缩放因子
            scale_factor = dpi_x / 96.0
            if scale_factor > 1.0:
                self.root.tk.call("tk", "scaling", scale_factor)
        except Exception:
            pass  # 获取失败时使用默认缩放，不影响正常使用

    def run(self):
        """启动应用"""
        self.root.mainloop()
