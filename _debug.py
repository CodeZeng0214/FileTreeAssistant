"""临时诊断脚本"""
import sys
sys.dont_write_bytecode = True

# 读取第148行
with open(__file__.replace("_debug.py", "ui.py"), "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i in range(146, 152):
        print(f"Line {i+1}: {lines[i].rstrip()}")
