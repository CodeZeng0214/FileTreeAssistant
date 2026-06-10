"""目录扫描核心模块 —— 递归扫描文件夹，支持深度控制和过滤"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FileNode:
    """文件/文件夹节点"""
    name: str
    path: str
    is_dir: bool
    level: int
    size: int = 0          # 文件大小（字节），文件夹为0
    modified_time: str = "" # 修改时间，格式 yyyy-MM-dd HH:mm
    children: list["FileNode"] = field(default_factory=list)


def _format_size(size_bytes: int) -> str:
    """将字节数格式化为人类可读的大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def scan_directory(
    root_path: str,
    max_depth: Optional[int] = None,
    show_folders: bool = True,
    show_files: bool = True,
    extensions: Optional[list[str]] = None,
) -> list[FileNode]:
    """
    递归扫描目录，返回节点列表（树形）。

    参数:
        root_path:   根目录路径
        max_depth:   最大扫描深度，None=不限制
        show_folders: 是否包含文件夹
        show_files:   是否包含文件
        extensions:   后缀过滤列表（如 ['.txt', '.py']），None=不过滤

    返回:
        FileNode 列表（第一层节点）
    """
    if not os.path.isdir(root_path):
        return []

    normalized_exts = None
    if extensions:
        normalized_exts = [e.strip().lower() if e.strip().startswith('.') 
                           else f'.{e.strip().lower()}' for e in extensions if e.strip()]

    def _scan(dir_path: str, current_depth: int) -> list[FileNode]:
        if max_depth is not None and current_depth > max_depth:
            return []

        nodes: list[FileNode] = []
        try:
            entries = sorted(os.scandir(dir_path), 
                           key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return nodes

        for entry in entries:
            child_level = current_depth
            stat = entry.stat()

            if entry.is_dir():
                children = _scan(entry.path, current_depth + 1) if show_folders else []
                if show_folders or (show_files and children):
                    node = FileNode(
                        name=entry.name,
                        path=entry.path,
                        is_dir=True,
                        level=child_level,
                        modified_time=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        children=children,
                    )
                    nodes.append(node)
            elif entry.is_file():
                if not show_files:
                    continue
                if normalized_exts:
                    _, ext = os.path.splitext(entry.name)
                    if ext.lower() not in normalized_exts:
                        continue
                node = FileNode(
                    name=entry.name,
                    path=entry.path,
                    is_dir=False,
                    level=child_level,
                    size=stat.st_size,
                    modified_time=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                )
                nodes.append(node)

        return nodes

    return _scan(root_path, 1)


def format_as_tree(nodes: list[FileNode], root_path: str = "") -> str:
    """
    将节点列表格式化为树形缩进文本。

    参数:
        nodes:     FileNode 列表
        root_path: 根路径（用于显示在顶部）

    返回:
        格式化的树形文本字符串
    """
    lines: list[str] = []
    if root_path:
        lines.append(os.path.basename(root_path.rstrip(os.sep)) + "/")

    def _format(nodes: list[FileNode], prefix: str, is_last_list: list[bool]):
        for i, node in enumerate(nodes):
            is_last = (i == len(nodes) - 1)
            connector = "└── " if is_last else "├── "
            line = prefix + connector + node.name
            lines.append(line)

            if node.children:
                child_prefix = prefix + ("    " if is_last else "│   ")
                _format(node.children, child_prefix, is_last_list + [is_last])

    _format(nodes, "", [])
    return "\n".join(lines)


def flatten_nodes(nodes: list[FileNode]) -> list[FileNode]:
    """
    将嵌套的树形节点展平为列表（用于 Excel 导出等）。
    按深度优先顺序展开。
    """
    flat: list[FileNode] = []

    def _walk(node_list: list[FileNode]):
        for node in node_list:
            flat.append(node)
            if node.children:
                _walk(node.children)

    _walk(nodes)
    return flat


def get_statistics(nodes: list[FileNode]) -> dict:
    """统计节点信息：文件数、文件夹数"""
    flat = flatten_nodes(nodes)
    file_count = sum(1 for n in flat if not n.is_dir)
    dir_count = sum(1 for n in flat if n.is_dir)
    total_size = sum(n.size for n in flat if not n.is_dir)
    return {
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size": total_size,
        "total_size_str": _format_size(total_size),
    }
