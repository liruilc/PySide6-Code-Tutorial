import os
import pathlib
from os import popen

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

# 配置项
Git_Ignore_File = os.path.join(project_dir, ".gitignore")
Project_Root_Path = project_dir
CLOC_PATH = r"C:\Users\ptylj\.vscode\my_app\cloc-2.04.exe"  # 使用实际的 cloc.exe 路径
# 配置项完

def cloc(gitignore_file: str = ".gitignore") -> None:
    """
    使用cloc统计项目代码行数 \n
    :param gitignore_file: gitignore文件路径
    :return: None
    """
    if not os.path.exists(CLOC_PATH):
        print(f"错误: 未找到 cloc.exe，请确认路径: {CLOC_PATH}")
        return

    if not os.path.exists(gitignore_file):
        print(f"错误: 未找到 .gitignore 文件，路径: {gitignore_file}")
        return

    print(f"正在使用的 .gitignore 文件路径: {gitignore_file}")
    print(f"项目根目录路径: {Project_Root_Path}")

    ignored_dir = ""
    gitignore_file_p = pathlib.Path(gitignore_file)
    with gitignore_file_p.open("r", encoding="UTF-8") as f:
        for dir_name in f.readlines():
            if not dir_name.startswith("#") and dir_name.strip():
                dir_name = dir_name.replace("/", "").replace("\n", ",")
                ignored_dir += dir_name

    # 使用完整路径调用cloc
    cmd = f"\"{CLOC_PATH}\" --exclude-dir {ignored_dir} \"{Project_Root_Path}\""
    print(f"\n执行的命令: {cmd}\n")

    try:
        with popen(cmd) as p:
            cmd_result = p.read()
            print(cmd_result)  # 直接打印完整结果

    except Exception as e:
        print(f"执行过程中出错: {str(e)}")

if __name__ == "__main__":
    cloc(Git_Ignore_File)