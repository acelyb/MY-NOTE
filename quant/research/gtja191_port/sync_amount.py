"""
amount/VWAP 通用数据源（增量+校验入口）。

定位：把 gtja191_port 的离线 amount 层（fetch_amount.py 全量首次拉 + data_amt/ 缓存）
升级成可长期复用的通用数据源，供资金流/VWAP 类新因子在 offline 层消费。

设计（复用既有，零改 fetch_amount.py / 零改 quant_system）：
- 全量：委托 fetch_amount.main()（或 --full 显式触发），首次/刷新用。
- 增量：对已有缓存只拉 last_date+1 → today 补新，复用 fetch_amount 的
  _fetch_one / _atomic_write / 防限流（BAN 暂停、退避）语义。
- 校验：--check 模式只读扫描 data_amt，报告每只的末日期/行数/缺失/无 amount，
  便于评估数据新鲜度与覆盖率，不拉网。
- 目录：AMT_DIR（data_amt/），独立于 quant_system/data/cache，绝不写其缓存。
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

PORT = Path(__file__).resolve().parent
sys.path.insert(0, str(PORT))

import fetch_amount  # 复用 _fetch_one / _atomic_write / AMT_DIR / BAN_MARKERS 等
from fetch_amount import AMT_DIR, ADJUST, START, WORKERS, THROTTLE, BAN_PAUSE, _atomic_write
from cache_reader import load_constituents


def _cache_file(symbol: str) -> Path:
    return AMT_DIR / f"stock_{symbol}_{ADJUST}_{START}.parquet"


def _last_date_of(symbol: str) -> str | None:
    """读已有 amount 缓存的末日期（YYYY-MM-DD），无缓存返回 None。"""
    p = _cache_file(symbol)
    if not p.exists():
        return None
    try:
        df = pd.read_parquet(p)
        if df.empty or "date" not in df.columns:
            return None
        return str(pd.Timestamp(df["date"].iloc[-1]))[:10]
    except Exception:
        return None


def _fetch_one_incremental(symbol: str, last_date: str) -> tuple[str, pd.DataFrame | None, str]:
    """拉 last_date 之后到今天的 amount 增量。带防限流（同 fetch_amount._fetch_one）。
    返回 (sym, 增量df, msg)。df 列与全量一致（date/open/high/low/close/volume/amount）。
    """
    import akshare as ak
    prefix = "sh" if symbol.startswith("6") else "sz"
    start_yyyymmdd = last_date.replace("-", "")
    for attempt in range(3):
        try:
            time.sleep(THROTTLE)
            # 新浪日线端点支持 start_date；增量从 last_date 拉，去重由调用方 merge 处理
            df = ak.stock_zh_a_daily(symbol=f"{prefix}{symbol}",
                                     start_date=start_yyyymmdd,
                                     end_date=time.strftime("%Y%m%d"), adjust=ADJUST)
            if df is None or df.empty:
                return symbol, None, "空返回(疑似封禁或停牌或无新数据)"
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            cols = [c for c in ["date", "open", "high", "low", "close", "volume", "amount"] if c in df.columns]
            df = df[cols].sort_values("date").reset_index(drop=True)
            if "amount" not in df.columns:
                return symbol, None, "无amount列"
            df = df[df["volume"] != 0].reset_index(drop=True)
            return symbol, df, "ok"
        except Exception as e:
            msg = str(e)
            if any(m.lower() in msg.lower() for m in fetch_amount.BAN_MARKERS):
                return symbol, None, f"BAN:{msg[:50]}"
            if attempt < 2:
                time.sleep([5, 15][attempt])
                continue
            return symbol, None, f"ERR:{msg[:60]}"
    return symbol, None, "重试用尽"


def _merge_incremental(symbol: str, inc: pd.DataFrame, last_date: str) -> pd.DataFrame:
    """把增量 inc 合并进已有缓存（去重保 last），返回合并后 df；无缓存则直接返回 inc。"""
    p = _cache_file(symbol)
    if p.exists():
        try:
            cached = pd.read_parquet(p)
        except Exception:
            cached = pd.DataFrame()
    else:
        cached = pd.DataFrame()
    if not cached.empty and "date" in cached.columns:
        merged = pd.concat([cached, inc], ignore_index=True)
        merged = merged.drop_duplicates(subset=["date"], keep="last")
        merged = merged.sort_values("date").reset_index(drop=True)
        return merged
    return inc.sort_values("date").reset_index(drop=True)


def incremental(symbols: list[str], progress: bool = True) -> None:
    """对已有缓存做增量更新（无缓存则委托全量）。"""
    # 无缓存的标的需要全量：委托 fetch_amount._fetch_one
    need_full = [s for s in symbols if _cache_file(s).exists() is False]
    # 有缓存的走增量
    need_inc = [s for s in symbols if s not in need_full]
    ban_until = 0.0

    if need_full:
        print(f"缺缓存 {len(need_full)} 只 → 全量拉取", flush=True)
        # 复用 fetch_amount 的全量逻辑：逐个 _fetch_one + 原子写
        ban_until = 0.0
        ok = fail = 0
        def _one(sym):
            nonlocal ban_until
            if time.time() < ban_until:
                time.sleep(ban_until - time.time())
            return fetch_amount._fetch_one(sym)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(_one, s): s for s in need_full}
            for i, fut in enumerate(as_completed(futs), 1):
                sym, df, msg = fut.result()
                if df is not None:
                    _atomic_write(_cache_file(sym), df)
                    ok += 1
                elif msg.startswith("BAN"):
                    ban_until = time.time() + BAN_PAUSE
                    fail += 1
                else:
                    fail += 1
                if progress and (i % 50 == 0 or i == len(need_full)):
                    print(f"  全量[{i}/{len(need_full)}] ok={ok} fail={fail}", flush=True)
        print(f"  全量完成: ok={ok} fail={fail}", flush=True)

    if need_inc:
        print(f"增量 {len(need_inc)} 只", flush=True)
        ok = fail = fresh = 0
        # 单线程串行增量：低频操作无需并发，绕开并发读-改-写缓存竞态（原子写保证不损坏，
        # 但并发下"读旧缓存→merge→写"可能互相覆盖，串行消除此竞态）。
        for i, sym in enumerate(need_inc, 1):
            if time.time() < ban_until:
                time.sleep(ban_until - time.time())
            last = _last_date_of(sym)
            _, df, msg = _fetch_one_incremental(sym, last)
            if df is not None and not df.empty:
                merged = _merge_incremental(sym, df, last)
                _atomic_write(_cache_file(sym), merged)
                ok += 1
            elif df is not None and df.empty:
                fresh += 1  # 无新数据
            elif msg.startswith("BAN"):
                ban_until = time.time() + BAN_PAUSE
                fail += 1
            else:
                fail += 1
            if progress and (i % 50 == 0 or i == len(need_inc)):
                print(f"  增量[{i}/{len(need_inc)}] ok={ok} fresh={fresh} fail={fail} "
                      f"ban_pause_until={'on' if time.time()<ban_until else 'off'}", flush=True)
        print(f"  增量完成: ok={ok} fresh(无新数据)={fresh} fail={fail}", flush=True)


def check(symbols: list[str], limit: int = 20) -> None:
    """只读校验 data_amt：报告覆盖率、末日期分布、行数、无 amount。不拉网。"""
    missing = [s for s in symbols if not _cache_file(s).exists()]
    present = [s for s in symbols if _cache_file(s).exists()]
    no_amount = []
    last_dates = []
    rows = []
    for s in present:
        try:
            df = pd.read_parquet(_cache_file(s))
            if "amount" not in df.columns or df["amount"].isna().all():
                no_amount.append(s)
            last_dates.append(str(pd.Timestamp(df["date"].iloc[-1]))[:10])
            rows.append(len(df))
        except Exception:
            no_amount.append(s)
    print(f"成分股 {len(symbols)} / 有缓存 {len(present)} / 缺失 {len(missing)} / 无amount {len(no_amount)}", flush=True)
    if present:
        from collections import Counter
        dist = Counter(last_dates)
        print("末日期分布(前10):")
        for d, c in sorted(dist.items(), reverse=True)[:10]:
            print(f"  {d}: {c}只", flush=True)
        print(f"行数 range: {min(rows)}-{max(rows)}, 中位 {sorted(rows)[len(rows)//2]}", flush=True)
    if missing:
        print(f"缺失示例: {missing[:10]}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", default="csi1000")
    ap.add_argument("--mode", choices=["inc", "full", "check"], default="inc",
                    help="inc=增量更新(默认), full=全量重拉, check=只读校验")
    ap.add_argument("--limit", type=int, default=0, help="只处理前N只(调试用, 0=全部)")
    args = ap.parse_args()

    syms = load_constituents(args.universe)
    if args.limit > 0:
        syms = syms[:args.limit]
    print(f"universe={args.universe}, 处理 {len(syms)} 只, mode={args.mode}", flush=True)

    if args.mode == "check":
        check(syms, limit=args.limit)
    elif args.mode == "full":
        # 显式全量：委托 fetch_amount 的 main() 逻辑（它按 csi1000 断点续传）
        sys.argv = [sys.argv[0], "--universe", args.universe, "--limit", str(args.limit)]
        fetch_amount.main()
    else:
        incremental(syms, progress=True)


if __name__ == "__main__":
    main()
