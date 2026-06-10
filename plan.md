# FileTreeAssistant — 文件目录树助手 需求方案

**TL;DR**: 用 Python + tkinter 开发一个 Windows 桌面工具，扫描文件夹目录结构（支持深度控制和文件过滤），结果以树形展示，支持复制剪贴板、导出 TXT/Excel，PyInstaller 打包为 .exe。

---

## 核心需求确认

| 需求项     | 决策                                           |
| ---------- | ---------------------------------------------- |
| 技术栈     | Python 3 + tkinter（内置，零依赖）             |
| GUI 美化   | ttkbootstrap 主题库（轻量，支持淡蓝风格）      |
| 界面展示   | 树形缩进显示（类似 `├──` `│   ` 结构） |
| TXT 导出   | 树形缩进纯文本                                 |
| Excel 导出 | 表格形式，可选基础/完整两种列结构              |
| 基础列     | 层级、名称、类型（文件/文件夹）、完整路径      |
| 完整列     | 基础列 + 文件大小 + 修改日期                   |
| 文件过滤   | ☑显示文件夹 ☑显示文件 + 后缀筛选输入框       |
| 深度控制   | 数字输入，默认不限制（最大深度）               |
| 包管理     | uv（`uv add` / `uv run`）                  |
| 打包形式   | PyInstaller 打包为单个 .exe                    |

---

## 项目结构

FileTreeAssistant/
├── main.py                 # 程序入口
├── scanner.py              # 目录扫描核心逻辑
├── ui.py                   # tkinter UI 界面
├── exporter.py             # TXT / Excel 导出
├── pyproject.toml          # uv 项目配置 + 依赖
├── build.bat               # 一键打包脚本
└── README.md               # 使用说明
-----------------------------------------

## 实现步骤

### 阶段 1：核心扫描模块（scanner.py）

1. 实现 `scan_directory(root_path, max_depth, show_folders, show_files, extensions)` 函数
   - 参数：根路径、最大深度（None=不限制）、是否显示文件夹、是否显示文件、后缀过滤列表
   - 返回：嵌套的目录节点列表，每个节点含 name, type, path, level, size, modified_time
   - 使用 `os.scandir` 递归，按深度控制
2. 实现 `format_as_tree(nodes)` 函数，格式化为树形缩进文本（`├──` `│   ` `└──`）

### 阶段 2：UI 界面（ui.py）

1. 主窗口：标题 "文件树助手"，尺寸 900×650，淡蓝色主题
2. 顶部操作栏（水平排列）：
   - 文件夹路径输入框 + 浏览按钮
   - 深度输入（Spinbox，默认值"不限制"）
   - 扫描按钮（蓝色高亮）
3. 过滤面板（可折叠）：
   - 复选框：☑ 显示文件夹 / ☑ 显示文件
   - 后缀筛选输入框（提示：如 .txt,.py，留空=全部）
4. 结果展示区（Text 控件，等宽字体 Consolas，占主体）
5. 底部操作栏：
   - 复制到剪贴板 / 导出 TXT / 导出 Excel（弹窗选基础/完整）
   - 状态栏显示扫描统计

### 阶段 3：导出模块（exporter.py）

1. TXT 导出：树形文本 → filedialog 选择路径 → 写入 .txt
2. Excel 导出（openpyxl）：
   - 基础列：层级 | 名称 | 类型 | 完整路径
   - 完整列：层级 | 名称 | 类型 | 大小 | 修改日期 | 完整路径
   - 表头加粗 + 淡蓝背景 + 自动列宽

### 阶段 4：剪贴板与打包

1. 剪贴板：pyperclip 实现复制
2. 打包：`uv run pyinstaller --onefile --windowed main.py`
3. build.bat 一键打包脚本

---

## 依赖

| 库           | 用途     | 安装                    |
| ------------ | -------- | ----------------------- |
| tkinter      | GUI      | Python 内置             |
| ttkbootstrap | 主题美化 | `uv add ttkbootstrap` |
| openpyxl     | Excel    | `uv add openpyxl`     |
| pyperclip    | 剪贴板   | `uv add pyperclip`    |
| PyInstaller  | 打包     | `uv add pyinstaller`  |

---

## UI 风格

- 主色调：淡蓝（#E3F2FD 背景 / #42A5F5 强调）
- 字体：微软雅黑（界面）+ Consolas（树形显示）
- 布局：顶部操作 → 中部结果 → 底部导出

---

## 验证步骤

1. 选测试文件夹扫描，确认树形显示正确
2. 改深度值（1/2/3），确认层级限制生效
3. 取消"显示文件夹"，确认只显示文件
4. 后缀过滤 .txt，确认筛选生效
5. 复制到剪贴板 → 粘贴到记事本验证
6. 导出 TXT 并打开验证
7. 导出 Excel（基础/完整）并打开验证
8. build.bat 打包为 exe，在另一台电脑测试

---

## 边界

- ✅ 包含：单文件夹扫描、深度控制、文件过滤、剪贴板、TXT/Excel 导出、exe 打包
- ❌ 不含：多文件夹对比、内容搜索、正则过滤、网络路径、右键集成、自动刷新

---
