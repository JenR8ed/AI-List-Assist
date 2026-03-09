import sys
try:
    with open("app_enhanced.py", "r") as f:
        content = f.read()
    compile(content, "app_enhanced.py", "exec")
    print("Syntax OK")
except Exception as e:
    print(e)
