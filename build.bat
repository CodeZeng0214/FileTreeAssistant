@echo off
chcp 65001 >nul
echo ========================================
echo   FileTreeAssistant — 打包为 EXE
echo ========================================
echo.

REM 清理旧的构建文件
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [1/2] 正在使用 PyInstaller 打包...
uv run pyinstaller ^
    --onefile ^
    --windowed ^
    --name "文件树助手" ^
    --add-data "scanner.py;." ^
    --add-data "exporter.py;." ^
    --add-data "ui.py;." ^
    --hidden-import ttkbootstrap ^
    --hidden-import openpyxl ^
    --hidden-import pyperclip ^
    --clean ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 打包失败！请检查错误信息。
    pause
    exit /b 1
)

echo.
echo [2/2] 打包完成！
echo.
echo 📦 输出文件：dist\文件树助手.exe
echo.
echo 你可以将 文件树助手.exe 复制到任意位置双击运行。
echo ========================================
pause
