"""
测试 MiniMax MCP Web Search 功能
"""
import json
import subprocess
import sys
import time
import os

def test_mcp_web_search():
    """测试 MiniMax MCP 的 web_search 工具"""
    
    # 测试查询
    test_queries = [
        "2026年2月12日 A股收盘",
        "MiniMax 人工智能",
        "Cursor IDE 使用教程"
    ]
    
    print("=" * 60)
    print("MiniMax MCP Web Search 测试")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n测试 {i}: {query}")
        print("-" * 40)
        
        # 构建请求
        request = {
            "jsonrpc": "2.0",
            "id": i,
            "method": "tools/call",
            "params": {
                "name": "web_search",
                "arguments": {
                    "query": query
                }
            }
        }
        
        print(f"请求: {json.dumps(request, ensure_ascii=False, indent=2)}")
        
        # 由于 MCP 连接有问题，我们先用 API 直接测试
        print("\n尝试直接调用 MiniMax API...")
        
        # 读取配置
        config_file = r"D:\AI_Workspace\config\mcporter.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config["mcpServers"]["MiniMax"]["env"]["MINIMAX_API_KEY"]
                api_host = config["mcpServers"]["MiniMax"]["env"]["MINIMAX_API_HOST"]
                
            print(f"API Host: {api_host}")
            print(f"API Key: {api_key[:20]}...")
            
        except Exception as e:
            print(f"读取配置失败: {e}")
            return
        
        # 尝试调用 MCP 服务器
        print("\n尝试启动 MCP 服务器...")
        
        env = os.environ.copy()
        env["MINIMAX_API_KEY"] = api_key
        env["MINIMAX_API_HOST"] = api_host
        env["MINIMAX_MCP_BASE_PATH"] = r"D:\AI_Workspace\mcp-output"
        
        try:
            # 启动 MCP 服务器
            proc = subprocess.Popen(
                [r"C:\Users\Administrator\.local\bin\uvx.EXE", "minimax-coding-plan-mcp"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待启动
            time.sleep(5)
            
            # 检查进程状态
            if proc.poll() is not None:
                stdout, stderr = proc.communicate()
                print(f"进程已退出 (code: {proc.returncode})")
                print(f"stdout: {stdout[:500] if stdout else 'N/A'}")
                print(f"stderr: {stderr[:500] if stderr else 'N/A'}")
            else:
                print("MCP 服务器正在运行")
                print(f"PID: {proc.pid}")
                
                # 尝试发送请求
                print("\n尝试发送 MCP 请求...")
                request_str = json.dumps(request) + "\n"
                try:
                    stdout, stderr = proc.communicate(input=request_str, timeout=10)
                    print(f"响应: {stdout[:1000] if stdout else 'N/A'}")
                    if stderr:
                        print(f"stderr: {stderr[:500]}")
                except subprocess.TimeoutExpired:
                    print("请求超时")
                    proc.kill()
                
        except Exception as e:
            print(f"错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

def test_api_directly():
    """直接测试 MiniMax API"""
    print("\n" + "=" * 60)
    print("直接测试 MiniMax API")
    print("=" * 60)
    
    import requests
    
    config_file = r"D:\AI_Workspace\config\mcporter.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            api_key = config["mcpServers"]["MiniMax"]["env"]["MINIMAX_API_KEY"]
            api_host = config["mcpServers"]["MiniMax"]["env"]["MINIMAX_API_HOST"]
    except Exception as e:
        print(f"读取配置失败: {e}")
        return
    
    # 测试不同的 endpoint
    endpoints = [
        f"https://{api_host}/v1/text/chatcompletion_v2",
    ]
    
    for url in endpoints:
        print(f"\n测试 endpoint: {url}")
        try:
            data = {
                "model": "MiniMax-M2.1",
                "messages": [
                    {"role": "system", "content": "你是一个搜索助手，请用简短的方式回答用户问题"},
                    {"role": "user", "content": "今天A股收盘情况怎么样？上证指数涨了多少？"}
                ],
                "max_tokens": 500,
                "temperature": 0.7
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("MiniMax MCP 测试脚本")
    print("1. 测试 MCP Web Search")
    print("2. 直接测试 API")
    print("3. 退出")
    
    choice = input("\n请选择 (1/2/3): ").strip()
    
    if choice == "1":
        test_mcp_web_search()
    elif choice == "2":
        test_api_directly()
    else:
        print("退出")
