"""Fix ui.py - remove padding from LabelFrame"""
filepath = "ui.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix: remove padding from LabelFrame and add result_inner
old = 'result_frame = ttkb.LabelFrame(main_frame, text="\U0001f4cb' + ' \u626b\u63cf\u7ed3\u679c", padding=(8, 6))'
new = 'result_frame = ttkb.LabelFrame(main_frame, text="\U0001f4cb' + ' \u626b\u63cf\u7ed3\u679c")\n        result_inner = ttkb.Frame(result_frame, padding=(8, 6))\n        result_inner.pack(fill=BOTH, expand=YES)'

if old in content:
    print("Found padding on LabelFrame, fixing...")
    content = content.replace(old, new, 1)
    
    # Fix Text parent
    content = content.replace(
        '            result_frame,',
        '            result_inner,'
    )
    
    # Fix scrollbar parents
    content = content.replace(
        'ttkb.Scrollbar(result_frame, orient=VERTICAL',
        'ttkb.Scrollbar(result_inner, orient=VERTICAL'
    )
    content = content.replace(
        'ttkb.Scrollbar(result_frame, orient=HORIZONTAL',
        'ttkb.Scrollbar(result_inner, orient=HORIZONTAL'
    )
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found, checking...")
    # Find any LabelFrame with padding
    for i, line in enumerate(content.split('\n'), 1):
        if 'LabelFrame' in line and 'padding' in line:
            print(f"Line {i}: {line.strip()[:80]}")
