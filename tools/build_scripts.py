# -*- coding: utf-8 -*-
"""
【开发辅助工具】把 tools\\bat_src\\ 里的 UTF-8 源脚本一键转换为
Windows 双击可用的 GBK + CRLF 版本，输出到 scripts\\ 目录。

为什么需要它：
  - 用户电脑是中文 Windows（控制台代码页 936），.bat 需要 GBK 编码 + CRLF 行尾
  - 源文件用 UTF-8 + LF 保存更通用（git、编辑器友好）
  - 编码/行尾转换必须由本脚本一步到位完成
    （经 sed/iconv 等多工具往返会损坏文件 —— 已踩过坑）

用法（改完 tools\\bat_src 里的脚本后运行一次）：
    python tools\\build_scripts.py
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent
SRC = BASE / "bat_src"
DST = BASE.parent / "scripts"


def main() -> int:
    if not SRC.is_dir():
        print(f"[错误] 找不到源目录：{SRC}")
        return 1
    DST.mkdir(parents=True, exist_ok=True)

    count = 0
    for src_file in sorted(SRC.glob("*.bat")):
        text = src_file.read_text(encoding="utf-8")
        # 统一行尾为 Windows 格式（先归一到 \n，再整体转 \r\n，避免出现 \r\r\n）
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
        data = text.encode("gbk")  # 中文 Windows 控制台默认代码页 936
        out_file = DST / src_file.name
        out_file.write_bytes(data)
        print(f"  已生成 scripts\\{src_file.name}  ({len(data)} 字节)")
        count += 1

    print(f"\n完成：共 {count} 个脚本已更新到 scripts\\ 目录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
