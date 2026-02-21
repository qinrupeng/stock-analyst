import os
os.chdir(r'D:/AI_Workspace/stock_agent')

files = sorted([f for f in os.listdir('.') if f.endswith('.md')])
for f in files:
    print(f"\n{'='*60}")
    print(f"文件: {f}")
    print('='*60)
    content = open(f, 'r', encoding='utf-8').read()
    
    # 保存到临时文件，避免打印编码问题
    temp_file = f.replace('.md', '_content.txt')
    open(temp_file, 'w', encoding='utf-8').write(content)
    print(f"内容已保存到: {temp_file} ({len(content)} chars)")
