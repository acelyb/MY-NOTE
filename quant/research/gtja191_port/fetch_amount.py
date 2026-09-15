"""为 41 个 VWAP 因子补 amount(成交额)列 —— 走正路, 不近似。

数据源: akshare 新浪日线 stock_zh_a_daily (与 quant_system 同款端点, 该端点返回 amount 列,
但 quant_system 的 _normalize 主动丢弃了 amount, 故这里独立拉取)。
VWAP = amount / volume 精确反推 (非典型价近似)。

防限流设计 (memory: 分钟端点 stock_zh_a_minute 会被小时级长封, 日线端点不受影响;
仍保守处理):
- 低并发: 4 线程 (quant_system 默认 8, 这里更保守)。
- 节流: 每只请求前 time.sleep(0.3)。
- 失败重试: 指数退避 3 次 (5s/15s/30s); 遇封禁特征(429/空/超时)整体暂停 60s 再续。
- 独立缓存目录 data_amt/, 绝不写 quant_system/data/cache, 不碰其源码与缓存。

缓存键复刻 quant_system: stock_{sym}_qfq_2020-01-01.parquet, 但列含 amount。
日期范围对齐现有日线: 2020-01-01 → 今天。
"""
from __future__ import annotations
import sys, time, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

PORT = Path("/home/cambricon/Documents/code/survey/gtja191_port")
sys.path.insert(0, str(PORT))
from cache_reader import load_constituents

AMT_DIR = PORT / "data_amt"
AMT_DIR.mkdir(parents=True, exist_ok=True)
START = "2020-01-01"
END = time.strftime("%Y%m%d")
ADJUST = "qfq"
WORKERS = 4
THROTTLE = 0.3  # 每只请求间隔秒
BAN_PAUSE = 60  # 疑似封禁整体暂停秒

BAN_MARKERS = ("429", "too many", "请求过于频繁", "Blocked", "forbidden", "Your Connection")

def _fetch_one(symbol: str) -> tuple[str, pd.DataFrame | None, str]:
    """拉单只 amount, 返回 (sym, df, msg)。df 含 date/open/high/low/close/volume/amount。"""
    import akshare as ak
    prefix = "sh" if symbol.startswith("6") else "sz"
    for attempt in range(3):
        try:
            time.sleep(THROTTLE)
            df = ak.stock_zh_a_daily(symbol=f"{prefix}{symbol}",
                                     start_date=START.replace("-", ""),
                                     end_date=END, adjust=ADJUST)
            if df is None or df.empty:
                return symbol, None, "空返回(疑似封禁或停牌)"
            # 标准列 + amount
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            cols = [c for c in ["date","open","high","low","close","volume","amount"] if c in df.columns]
            df = df[cols].sort_values("date").reset_index(drop=True)
            if "amount" not in df.columns:
                return symbol, None, "无amount列"
            df = df[df["volume"] != 0].reset_index(drop=True)  # 同 quant_system 口径丢 vol=0
            return symbol, df, "ok"
        except Exception as e:
            msg = str(e)
            if any(m.lower() in msg.lower() for m in BAN_MARKERS):
                return symbol, None, f"BAN:{msg[:50]}"
            if attempt < 2:
                time.sleep([5, 15][attempt])  # 退避 5s, 15s
                continue
            return symbol, None, f"ERR:{msg[:60]}"
    return symbol, None, "重试用尽"

def main():
    syms = load_constituents("csi1000")
    # 跳过已有缓存(断点续传)
    todo = [s for s in syms if not (AMT_DIR / f"stock_{s}_{ADJUST}_{START}.parquet").exists()]
    print(f"csi1000: {len(syms)} 只, 已缓存 {len(syms)-len(todo)}, 待拉 {len(todo)}", flush=True)
    if not todo:
        print("全部已缓存, 无需拉取", flush=True)
        return

    ok = fail = ban = 0
    fail_syms = []
    t0 = time.time()
    ban_until = 0.0  # 封禁暂停截止时间

    def _one(sym):
        nonlocal ban_until
        # 若处于封禁暂停期, 等待
        now = time.time()
        if now < ban_until:
            time.sleep(ban_until - now)
        return _fetch_one(sym)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_one, s): s for s in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            sym, df, msg = fut.result()
            if df is not None:
                _atomic_write(AMT_DIR / f"stock_{sym}_{ADJUST}_{START}.parquet", df)
                ok += 1
            elif msg.startswith("BAN"):
                ban += 1
                ban_until = time.time() + BAN_PAUSE  # 整体暂停 60s
                fail_syms.append((sym, msg))
            else:
                fail += 1
                fail_syms.append((sym, msg))
            if i % 50 == 0 or i == len(todo):
                el = time.time() - t0
                print(f"  [{i}/{len(todo)}] ok={ok} fail={fail} ban={ban} 用时{el:.0f}s ban_pause_until={'on' if time.time()<ban_until else 'off'}", flush=True)

    print(f"\n完成: ok={ok} fail={fail} ban={ban}, 总用时{time.time()-t0:.0f}s", flush=True)
    if fail_syms:
        print(f"失败/封禁 {len(fail_syms)} 只(前20):", flush=True)
        for s, m in fail_syms[:20]:
            print(f"  {s}: {m}", flush=True)

def _atomic_write(path: Path, df: pd.DataFrame):
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".parquet", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            df.to_parquet(f)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise

if __name__ == "__main__":
    main()
