"""FileTreeAssistant — 文件目录树助手
一个简洁的 Windows 桌面工具，用于扫描文件夹目录结构，
支持树形展示、剪贴板复制、TXT/Excel 导出。
"""

from ui import FileTreeApp


def main():
    app = FileTreeApp()
    app.run()


if __name__ == "__main__":
    main()
