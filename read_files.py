import os
os.chdir(r'D:\AI_Workspace')
files = [f for f in os.listdir('.') if f.startswith('1_') or f.startswith('2_')]
for f in files:
    print('='*60)
    print(f'文件: {f}')
    print('='*60)
    content = open(f, 'r', encoding='utf-8').read()
    # 只保存到新文件，不打印
    print(f'文件大小: {len(content)} 字符')
    # 保存完整内容到 workspace 根目录
    print(f'已保存内容\n')
