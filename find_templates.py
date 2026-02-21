import os

def find_files(directory, extension='.html'):
    """查找目录下所有指定扩展名的文件"""
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                html_files.append(os.path.join(root, file))
    return html_files

# 查找stock-fullstack-analyst目录下的HTML文件
skill_dir = r"D:\AI_Workspace\skills\stock-fullstack-analyst"
html_files = find_files(skill_dir, '.html')

print("找到的HTML文件：")
for f in html_files:
    print(f)
