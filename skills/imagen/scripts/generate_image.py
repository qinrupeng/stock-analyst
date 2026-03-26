#!/usr/bin/env python3
"""
Imagen - 火山引擎图像生成脚本

使用火山引擎OpenAI兼容API生成图片。
支持Windows、macOS和Linux。

用法：
    python generate_image.py "提示词" [输出路径]

环境变量：
    ARK_API_KEY (必需) - 火山引擎API密钥
    IMAGE_SIZE (可选) - 图片尺寸：4K (默认，模型自动匹配), 2K, 3K, 1280x720, 720x1280
    VOLCENGINE_MODEL (可选) - 模型ID (默认: doubao-seedream-5-0-260128)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("错误：需要安装openai库", file=sys.stderr)
    print("安装命令：pip install openai", file=sys.stderr)
    sys.exit(1)


# 配置
DEFAULT_MODEL_ID = "doubao-seedream-4-5-251128" #doubao-seedream-4-5-251128 doubao-seedream-5-0-260128
API_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_IMAGE_SIZE = "4K"  # 4K分辨率（模型自动匹配尺寸）
VALID_SIZES = {"1024x1024", "1280x720", "720x1280", "2K", "3K", "4K"}  # 4K


def get_api_key() -> str:
    """从环境变量获取火山引擎API密钥。"""
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("错误：ARK_API_KEY 环境变量未设置", file=sys.stderr)
        print("\n设置方法：", file=sys.stderr)
        print("  Windows (PowerShell): $env:ARK_API_KEY = '你的密钥'", file=sys.stderr)
        print("  Windows (CMD): set ARK_API_KEY=你的密钥", file=sys.stderr)
        print("  macOS/Linux: export ARK_API_KEY='你的密钥'", file=sys.stderr)
        print("\n获取密钥：https://www.volcengine.com/", file=sys.stderr)
        sys.exit(1)
    return api_key


def get_file_size(path: Path) -> str:
    """获取人类可读的文件大小。"""
    size = path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main():
    parser = argparse.ArgumentParser(
        description="使用火山引擎AI生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python generate_image.py "日落山脉风景"
  python generate_image.py "应用图标" ./icons/app.png
  python generate_image.py --size 2K "高分辨率风景" ./wallpaper.png
  python generate_image.py --model doubao-seedream-5-0-260128 "科技感logo" ./logo.png

环境变量：
  ARK_API_KEY         火山引擎API密钥（必需）
  IMAGE_SIZE          图片尺寸：1024x1024 (默认), 1280x720, 720x1280, 2K
  VOLCENGINE_MODEL    模型ID

图生图用法：
  python generate_image.py "将图片风格转为卡通" --ref original.png --output cartoon.png
  python generate_image.py "换一件衣服" --ref person.png clothes.png --output result.png

注意事项：
  - 图生图需要使用 doubao-seedream-5-0-260128 模型
  - --ref 支持多张参考图（最多4张）
  - 参考图可以是本地路径或URL
        """
    )
    parser.add_argument("prompt", help="要生成的图片的文本描述")
    parser.add_argument("output", nargs="?", default="reports\\images\\generated-image.png",
                        help="输出文件路径（默认：reports\\images\\generated-image.png，相对于工作空间根目录）")
    parser.add_argument("--size", "-s", choices=["1024x1024", "1280x720", "720x1280", "2K", "3K", "4K"],
                        help="图片尺寸（覆盖IMAGE_SIZE环境变量），默认4K（模型自动匹配尺寸）")
    parser.add_argument("--model", "-m",
                        help=f"模型ID（默认：{DEFAULT_MODEL_ID}）")
    parser.add_argument("--ref", "-r", nargs="+", default=[],
                        help="参考图片路径（支持多张，用于图生图）")
    parser.add_argument("--no-watermark", action="store_true",
                        help="不添加水印（默认）")

    args = parser.parse_args()

    # 获取配置
    api_key = get_api_key()
    model_id = args.model or os.environ.get("VOLCENGINE_MODEL", DEFAULT_MODEL_ID)
    image_size = args.size or os.environ.get("IMAGE_SIZE", DEFAULT_IMAGE_SIZE)
    output_path = Path(args.output)

    # 创建输出目录
    output_dir = output_path.parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # 处理参考图片（转Base64）
    ref_images = []
    if args.ref:
        import base64
        for ref_path in args.ref:
            ref_file = Path(ref_path)
            if ref_file.exists():
                with open(ref_file, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")
                    ref_images.append(f"data:image/png;base64,{img_data}")
            else:
                print(f"警告：参考图片不存在: {ref_path}", file=sys.stderr)
        print(f"参考图片：{len(ref_images)} 张")

    # 图生图模式尺寸处理：4K不支持，转为2k
    if ref_images and image_size == "4K":
        image_size = "2k"
        print(f"尺寸调整：图生图模式 4K → 2k")

    # 显示信息
    print(f"正在生成图片，提示词：\"{args.prompt}\"")
    print(f"模型：{model_id}")
    print(f"图片尺寸：{image_size}")
    print(f"输出路径：{output_path}")
    if ref_images:
        print(f"参考图：{len(ref_images)} 张（图生图模式）")
    print()

    # 初始化客户端
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=api_key
    )

    try:
        # 构建请求参数
        request_params = {
            "model": model_id,
            "prompt": args.prompt,
            "size": image_size,
            "response_format": "url",
        }

        # 根据模型和是否有参考图添加额外参数
        if ref_images:
            # 图生图模式（需要4系以上模型）
            request_params["extra_body"] = {
                "image": ref_images,
                "watermark": False,
            }
            if "doubao-seedream-5" in model_id:
                request_params["output_format"] = "png"
        elif "doubao-seedream-5" in model_id:
            # 5系模型文生图
            request_params["output_format"] = "png"
            request_params["extra_body"] = {"watermark": False}
        else:
            # 4系模型文生图
            request_params["extra_body"] = {"watermark": False}

        response = client.images.generate(**request_params)

        # 获取图片URL
        image_url = response.data[0].url

        if not image_url:
            print("错误：未从API获取到图片URL", file=sys.stderr)
            sys.exit(1)

        print(f"图片生成成功！")
        print(f"URL: {image_url}")

        # 下载图片并保存
        import urllib.request
        urllib.request.urlretrieve(image_url, output_path)

        # 验证并报告成功
        if output_path.exists() and output_path.stat().st_size > 0:
            file_size = get_file_size(output_path)
            print(f"图片已保存！")
            print(f"文件：{output_path}")
            print(f"大小：{file_size}")
        else:
            print(f"错误：保存图片到 {output_path} 失败", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
