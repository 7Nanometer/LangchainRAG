# -*- coding: utf-8 -*-
r"""
压测资源监控 —— 压测期间每秒记录一次系统资源，生成 CSV 供分析

记录内容：
  - 整机 CPU / 内存占用
  - 服务进程（uvicorn）的 CPU / 内存占用
  - 显卡利用率 / 显存占用（NVIDIA 卡）

用法（压测前在另一个窗口先启动本脚本）：
    python tests/stress_monitor.py 输出文件.csv 时长秒数
"""
import csv
import subprocess
import sys
import time
from datetime import datetime

import psutil


def _find_server_procs() -> list:
    """找到运行中的 uvicorn（服务）进程"""
    procs = []
    for p in psutil.process_iter(["name", "cmdline"]):
        try:
            if "python" not in (p.info["name"] or "").lower():
                continue
            cmd = " ".join(p.info["cmdline"] or [])
            if "uvicorn" in cmd:
                procs.append(p)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return procs


def _gpu_stats() -> tuple[float, float]:
    """读取显卡利用率(%)和显存占用(MB)；无显卡时返回 (-1, -1)"""
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip().splitlines()[0]
        util, mem = [float(x.strip()) for x in out.split(",")]
        return util, mem
    except Exception:  # noqa: BLE001
        return -1.0, -1.0


def main() -> int:
    out_file = sys.argv[1] if len(sys.argv) > 1 else "stress_resource.csv"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 900

    print(f"开始监控 {duration} 秒 → {out_file}")
    print("时间｜CPU%｜内存%｜服务CPU%｜服务内存MB｜GPU%｜显存MB")

    with open(out_file, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["time", "cpu_percent", "mem_percent", "server_cpu_percent",
             "server_mem_mb", "gpu_util", "gpu_mem_mb"]
        )

        start = time.time()
        # 第一轮 cpu_percent 需要预热，丢弃初始值
        psutil.cpu_percent(interval=None)

        while time.time() - start < duration:
            now = datetime.now().strftime("%H:%M:%S")
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent

            procs = _find_server_procs()
            server_cpu = 0.0
            server_mem = 0.0
            for p in procs:
                try:
                    server_cpu += p.cpu_percent(interval=None)
                    server_mem += p.memory_info().rss / 1024 / 1024
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            gpu_util, gpu_mem = _gpu_stats()

            writer.writerow(
                [now, round(cpu, 1), round(mem, 1), round(server_cpu, 1),
                 round(server_mem, 1), gpu_util, gpu_mem]
            )
            fh.flush()

            if int(time.time() - start) % 30 == 0:
                print(f"{now}｜{cpu:.0f}%｜{mem:.0f}%｜{server_cpu:.0f}%｜"
                      f"{server_mem:.0f}MB｜{gpu_util:.0f}%｜{gpu_mem:.0f}MB")

            time.sleep(1)

    print("监控结束")
    return 0


if __name__ == "__main__":
    sys.exit(main())
