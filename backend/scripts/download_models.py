# -*- coding: utf-8 -*-
"""
下载本地 AI 模型（从 ModelScope 国内源，速度快、无需翻墙）

本脚本下载两个模型：
  1. bge-large-zh-v1.5    —— 把文字变成「数字 DNA」的向量模型（约 1.3GB）
  2. bge-reranker-v2-m3   —— 检索结果精排模型（约 2.2GB）

特点：支持断点续传 —— 下载中断后重新运行本脚本即可接着下，不会从头开始。
"""
import sys
from pathlib import Path

# 模型存放目录（F 盘，E 盘空间不够）
MODELS_DIR = Path(r"F:\LangchainRAG-data\models")

# 要下载的模型清单：(ModelScope 模型 ID, 本地文件夹名)
MODELS = [
    ("BAAI/bge-large-zh-v1.5", "bge-large-zh-v1.5"),
    ("BAAI/bge-reranker-v2-m3", "bge-reranker-v2-m3"),
]


def main() -> int:
    try:
        from modelscope import snapshot_download
    except ImportError:
        print("[错误] 未安装 modelscope，请先运行「1-首次安装.bat」")
        return 1

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for model_id, folder_name in MODELS:
        local_dir = MODELS_DIR / folder_name
        print(f"\n==== 开始下载：{model_id} ====")
        print(f"     存放到：{local_dir}")
        try:
            snapshot_download(model_id, local_dir=str(local_dir))
        except Exception as exc:  # noqa: BLE001 —— 把任何下载异常都转成中文提示
            print(f"\n[失败] {model_id} 下载出错：{exc}")
            print("       网络中断很常见，重新运行本脚本会自动断点续传。")
            return 1
        print(f"[完成] {model_id}")

    print("\n====================================")
    print(" 两个模型全部下载完成！")
    print("====================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
