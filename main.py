"""FileTreeAssistant — 文件目录树助手
一个简洁的 Windows 桌面工具，用于扫描文件夹目录结构，
支持树形展示、剪贴板复制、TXT/Excel 导出、文件夹拖入识别。
"""

# PyInstaller 打包时需要检测到 tkinterdnd2（其包含 Tcl/Tk 扩展 DLL）
import tkinterdnd2  # noqa: F401

from ui import FileTreeApp


def main():
    app = FileTreeApp()
    app.run()


if __name__ == "__main__":
    main()
