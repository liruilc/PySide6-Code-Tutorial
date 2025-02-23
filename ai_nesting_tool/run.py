#!/usr/bin/env python3
import os
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

def ensure_static_directory():
    """确保static目录存在"""
    static_dir = os.path.join(current_dir, "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        print("已创建static目录")

if __name__ == "__main__":
    # 确保必要的目录存在
    ensure_static_directory()
    
    # 启动UI
    from src.ui import create_ui
    create_ui()