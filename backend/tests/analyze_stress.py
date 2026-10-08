# -*- coding: utf-8 -*-
r"""
压力测试结果分析工具 —— 把 Locust 与资源监控产出的 CSV / 日志
汇总成"一眼看得懂"的分档表格（10 / 25 / 50 / 100 人）。

用法（在 backend 目录执行）：
    python tests/analyze_stress.py

分析内容：
  1. 每轮总成绩单：各接口请求数、失败数、失败率、响应时间
  2. 阶梯曲线：每一档人数的吞吐量、失败数、累计成绩
  3. 资源曲线：每一档的整机 CPU、内存、服务进程、显卡占用
  4. 失败时间线：从服务日志里定位错误发生的时间与类型
  5. 服务端真实耗时：从数据库统计每一档回答一条问题的耗时（毫秒）
"""
import csv
import re
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path

LOGS = Path(r"F:\LangchainRAG-data\logs")
STRESS_DIR = Path(r"F:\LangchainRAG-data\stress-data")

# 阶梯曲线（秒，起→止，人数）
STAGES = [
    (0, 150, "10 人档"),
    (150, 330, "25 人档"),
    (330, 570, "50 人档"),
    (570, 780, "100 人档·前段"),
    (780, 960, "100 人档·后段"),
]

ROUNDS = {
    1: {
        "name": "第一轮（修复前）",
        "stats": "locust_stats.csv",
        "history": "locust_stats_history.csv",
        "resource": "stress-resource.csv",
        "server_log": "stress-server.log",
    },
    2: {
        "name": "第二轮（修复后）",
        "stats": "locust2_stats.csv",
        "history": "locust2_stats_history.csv",
        "resource": "stress-resource2.csv",
        "server_log": "stress-server2.log",
    },
}

# 数据库开始记录时间（用于过滤服务端耗时统计，避免混入其他测试）
DB_WINDOWS = {
    1: ("2026-10-08 18:22:00", "2026-10-08 18:40:00"),
    2: ("2026-10-08 18:38:41", "2026-10-08 19:00:00"),
}


def load_csv(path: Path):
    """读取 CSV（Locust 在 Windows 上输出 GBK 编码，做兼容）"""
    for enc in ("utf-8-sig", "gbk"):
        try:
            with path.open(encoding=enc, newline="") as f:
                return [r for r in csv.reader(f) if r]
        except UnicodeDecodeError:
            continue
    return []


def fmt_ms(v) -> str:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{v / 1000:.1f}s" if v >= 1000 else f"{v:.0f}ms"


def pct(values, q):
    if not values:
        return 0
    values = sorted(values)
    k = min(len(values) - 1, int(q * (len(values) - 1)))
    return values[k]


# ---------------------------------------------------------------------------
# 1. 总成绩单
# ---------------------------------------------------------------------------
def show_final(round_no: int):
    cfg = ROUNDS[round_no]
    rows = load_csv(LOGS / cfg["stats"])
    print(f"\n{'=' * 78}\n【第 {round_no} 轮】总成绩单 —— {cfg['name']}\n{'=' * 78}")
    if not rows:
        print("（找不到统计文件）")
        return
    hdr = rows[0]
    for r in rows[1:]:
        if len(r) < 22 or r[0] == "Type":
            continue
        typ, name = r[0], r[1]
        reqs, fails = int(float(r[2])), int(float(r[3]))
        rate = fails / reqs * 100 if reqs else 0
        med, avg = float(r[4]), float(r[5])
        p90, p99, mx = float(r[15]), float(r[18]), float(r[21])
        label = "汇总" if not typ else name
        print(
            f"{label:<34} 请求 {reqs:>5}  失败 {fails:>4}（{rate:>5.2f}%）"
            f"  中位 {fmt_ms(med):>7}  均值 {fmt_ms(avg):>7}  P90 {fmt_ms(p90):>7}  最大 {fmt_ms(mx):>8}"
        )


# ---------------------------------------------------------------------------
# 2. 阶梯曲线（从 history 的累计计数器算每一档的增量）
# ---------------------------------------------------------------------------
def load_history(round_no: int):
    """返回 (t0, 汇总序列, 分接口序列)；汇总序列元素 = (ts, user_count, cum_req, cum_fail, cur_rps, p50_col, tot_med_col)"""
    cfg = ROUNDS[round_no]
    rows = load_csv(LOGS / cfg["history"])
    if not rows:
        return None
    hdr = rows[0]
    ix = {n: i for i, n in enumerate(hdr)}
    agg, per_name = [], {}
    for r in rows[1:]:
        if len(r) < len(hdr) or r[0] == "Timestamp":
            continue
        name = r[3]
        try:
            ts = int(r[0])
            uc = int(r[1])
            cum_r = int(float(r[ix["Total Request Count"]]))
            cum_f = int(float(r[ix["Total Failure Count"]]))
            rps = float(r[ix["Requests/s"]])
        except (ValueError, KeyError):
            continue
        entry = (ts, uc, cum_r, cum_f, rps)
        if name == "Aggregated":
            agg.append(entry)
        else:
            per_name.setdefault(name, []).append(entry)
    if not agg:
        return None
    t0 = agg[0][0]
    return t0, agg, per_name


def stage_of(rel: float):
    for i, (a, b, _) in enumerate(STAGES):
        if a <= rel < b:
            return i
    return None


def show_stages(round_no: int, hist):
    print(f"\n{'=' * 78}\n【第 {round_no} 轮】阶梯曲线（10→25→50→100 人）\n{'=' * 78}")
    if not hist:
        print("（找不到历史数据）")
        return
    t0, agg, per_name = hist
    duration = agg[-1][0] - t0
    print(f"总时长 {duration} 秒\n")

    # 每一档：请求/失败增量、平均 rps、平均在线人数
    stat = {i: {"req": 0, "fail": 0, "rps": [], "uc": []} for i in range(len(STAGES))}
    prev = None
    for ts, uc, cr, cf, rps in agg:
        rel = ts - t0
        si = stage_of(rel)
        if si is None:
            prev = (cr, cf)
            continue
        if prev is not None:
            stat[si]["req"] += max(0, cr - prev[0])
            stat[si]["fail"] += max(0, cf - prev[1])
        stat[si]["rps"].append(rps)
        stat[si]["uc"].append(uc)
        prev = (cr, cf)

    print(f"{'档位':<14}{'人数':>5}{'请求':>6}{'失败':>6}{'失败率':>8}{'吞吐(请求/秒)':>14}")
    for i, (a, b, label) in enumerate(STAGES):
        s = stat[i]
        if not s["rps"]:
            continue
        fr = s["fail"] / s["req"] * 100 if s["req"] else 0
        print(
            f"{label:<14}{statistics.mean(s['uc']):>5.0f}{s['req']:>6}{s['fail']:>6}"
            f"{fr:>7.2f}%{statistics.mean(s['rps']):>14.2f}"
        )

    # 分接口失败分布
    print(f"\n分接口失败分布：")
    for name, series in per_name.items():
        stage_fail = {}
        prev = None
        for ts, uc, cr, cf, rps in series:
            rel = ts - t0
            si = stage_of(rel)
            if si is not None and prev is not None:
                d = max(0, cf - prev[1])
                if d:
                    stage_fail[si] = stage_fail.get(si, 0) + d
            prev = (cr, cf)
        if stage_fail:
            detail = "、".join(f"{STAGES[i][2]}×{n}" for i, n in sorted(stage_fail.items()))
            print(f"  {name}: {detail}")

    # 分接口吞吐（chat 是关键）
    print(f"\n分接口平均吞吐（请求/秒）：")
    for name, series in per_name.items():
        rps_by_stage = {i: [] for i in range(len(STAGES))}
        for ts, uc, cr, cf, rps in series:
            si = stage_of(ts - t0)
            if si is not None:
                rps_by_stage[si].append(rps)
        cells = []
        for i in range(len(STAGES)):
            v = statistics.mean(rps_by_stage[i]) if rps_by_stage[i] else 0
            cells.append(f"{STAGES[i][2]}={v:.2f}")
        print(f"  {name}: " + "  ".join(cells))


# ---------------------------------------------------------------------------
# 3. 资源曲线
# ---------------------------------------------------------------------------
def show_resources(round_no: int, hist):
    cfg = ROUNDS[round_no]
    rows = load_csv(LOGS / cfg["resource"])
    print(f"\n{'=' * 78}\n【第 {round_no} 轮】资源曲线（每一档的平均占用）\n{'=' * 78}")
    if not rows or not hist:
        print("（找不到资源数据）")
        return
    t0 = datetime.fromtimestamp(hist[0])
    buckets = {i: {"cpu": [], "mem": [], "scpu": [], "smem": [], "gpu": [], "gmem": []}
               for i in range(len(STAGES))}
    for r in rows[1:]:
        if len(r) < 7 or r[0] == "time":
            continue
        try:
            t = datetime.strptime(r[0], "%H:%M:%S").replace(year=t0.year, month=t0.month, day=t0.day)
            rel = (t - t0).total_seconds()
        except ValueError:
            continue
        si = stage_of(rel)
        if si is None:
            continue
        b = buckets[si]
        b["cpu"].append(float(r[1]))
        b["mem"].append(float(r[2]))
        b["scpu"].append(float(r[3]))
        b["smem"].append(float(r[4]))
        g = float(r[5])
        gm = float(r[6])
        if g >= 0:
            b["gpu"].append(g)
        if gm >= 0:
            b["gmem"].append(gm)

    print(f"{'档位':<14}{'整机CPU':>8}{'内存':>8}{'服务CPU':>9}{'服务内存':>10}{'显卡':>8}{'显存':>9}")
    for i, (a, bsec, label) in enumerate(STAGES):
        b = buckets[i]
        if not b["cpu"]:
            continue
        mean = lambda k: statistics.mean(b[k]) if b[k] else 0
        print(
            f"{label:<14}{mean('cpu'):>7.1f}%{mean('mem'):>7.1f}%{mean('scpu'):>8.1f}%"
            f"{mean('smem'):>9.0f}M{mean('gpu'):>7.1f}%{mean('gmem'):>8.0f}M"
        )


# ---------------------------------------------------------------------------
# 4. 失败时间线（从服务日志找连接池耗尽的报错）
# ---------------------------------------------------------------------------
TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")


def show_error_timeline(round_no: int):
    cfg = ROUNDS[round_no]
    path = LOGS / cfg["server_log"]
    print(f"\n{'=' * 78}\n【第 {round_no} 轮】失败时间线（服务端连接池超时 = QueuePool 报错）\n{'=' * 78}")
    if not path.exists():
        print("（找不到服务日志）")
        return
    text = path.read_text(encoding="gbk", errors="replace")
    cur_ts = None
    events = []
    per_minute = {}
    for line in text.splitlines():
        m = TS_RE.match(line)
        if m:
            cur_ts = m.group(1)
        if "QueuePool limit" in line:
            events.append(cur_ts)
            if cur_ts:
                key = cur_ts[:16]
                per_minute[key] = per_minute.get(key, 0) + 1
    if not events:
        print("（没有发现连接池超时错误）")
        return
    print(f"共 {len(events)} 次；第一次：{events[0]}；最后一次：{events[-1]}\n")
    for k in sorted(per_minute):
        print(f"  {k}  {per_minute[k]:>4} 次  {'#' * min(60, per_minute[k])}")


# ---------------------------------------------------------------------------
# 5. 服务端真实耗时（数据库里每条回答记录的 latency_ms）
# ---------------------------------------------------------------------------
def show_db_latency(round_no: int, hist):
    print(f"\n{'=' * 78}\n【第 {round_no} 轮】服务端实际耗时（从回答问题开始到答案写完，单位毫秒）\n{'=' * 78}")
    db_path = STRESS_DIR / "app.db"
    if not db_path.exists() or not hist:
        print("（找不到数据库）")
        return
    start, end = DB_WINDOWS[round_no]
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT created_at, latency_ms FROM messages "
            "WHERE role='assistant' AND latency_ms IS NOT NULL AND created_at >= ? AND created_at < ?",
            (start, end),
        ).fetchall()
    finally:
        con.close()
    if not rows:
        print("（窗口内没有数据）")
        return
    t0 = datetime.fromtimestamp(hist[0])
    buckets = {i: [] for i in range(len(STAGES))}
    for created_at, latency in rows:
        try:
            t = datetime.fromisoformat(created_at)
        except ValueError:
            continue
        si = stage_of((t - t0).total_seconds())
        if si is not None:
            buckets[si].append(float(latency))
    print(f"{'档位':<14}{'完成条数':>8}{'平均':>10}{'中位':>10}{'P90':>10}{'最大':>10}")
    for i, (a, b, label) in enumerate(STAGES):
        v = buckets[i]
        if not v:
            continue
        print(
            f"{label:<14}{len(v):>8}{statistics.mean(v):>9.0f}ms{pct(v, 0.5):>9.0f}ms"
            f"{pct(v, 0.9):>9.0f}ms{max(v):>9.0f}ms"
        )


def main():
    for round_no in (1, 2):
        hist = load_history(round_no)
        show_final(round_no)
        show_stages(round_no, hist)
        show_resources(round_no, hist)
        show_error_timeline(round_no)
        show_db_latency(round_no, hist)
    print("\n分析完成。")


if __name__ == "__main__":
    main()
