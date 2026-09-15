"""
缓存只读加载器 —— 从 quant_system 的 data/cache 读取 parquet，绝不拉网、绝不写。

设计原则（用户硬约束）：
- 不改 quant_system 源码，只读它的缓存数据，避免影响其他 agent。
- 选缓存文件时复刻 quant_system 的缓存键约定 stock_{sym}_{adjust}_{start}，
  优先读"纯键"文件（无日期区间后缀，即增量更新的主文件），它通常是最新最全的。
- 文件缺失/读不出 → 该标的跳过（不回退拉网），与 read_only=True 语义一致但更严格。

日线缓存列：date, open, high, low, close, volume（无 vwap、无 amount）。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

# quant_system 项目根（本目录在 .../survey/gtja191_port，quant 在 .../code/quant_system）
QUANT_ROOT = Path(__file__).resolve().parents[2] / "quant_system"
CACHE_DIR = QUANT_ROOT / "data" / "cache"

# 日线默认起始日（与 quant_system get_stock_daily 默认一致）
DEFAULT_START = "2020-01-01"


def load_constituents(universe: str = "csi1000") -> list[str]:
    """读成分股缓存 const_{universe}.parquet，返回 6 位代码列表。"""
    p = CACHE_DIR / f"const_{universe}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"成分股缓存不存在: {p}（需先在 quant_system 跑过该池）")
    return pd.read_parquet(p)["symbol"].astype(str).tolist()


def load_daily(symbol: str, adjust: str = "qfq") -> pd.DataFrame | None:
    """读单只股票日线缓存。返回 df[date,open,high,low,close,volume] 按日期升序，或 None。

    纯键文件 stock_{sym}_{adjust}_{start}.parquet 是增量主文件（最新最全）。
    同一 sym 可能有多个带日期区间后缀的历史文件（早期全量刷新遗留），只取纯键文件。
    """
    if len(symbol) == 6 and symbol[0] in ("5", "9"):
        # 5x/9x 是基金/港股，非股票日线；csi1000 成分股均为 0/3/6 开头 A 股，这里兜底跳过
        return None
    p = CACHE_DIR / f"stock_{symbol}_{adjust}_{DEFAULT_START}.parquet"
    if not p.exists():
        return None
    try:
        df = pd.read_parquet(p)
    except Exception:
        return None
    if df.empty or "close" not in df.columns:
        return None
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_batch_daily(symbols: list[str], adjust: str = "qfq") -> dict[str, pd.DataFrame]:
    """批量读日线缓存，返回 {symbol: df}，缺失的标的自动跳过（不拉网）。"""
    out = {}
    for s in symbols:
        df = load_daily(s, adjust)
        if df is not None and not df.empty:
            out[s] = df
    return out


# ============ VWAP 因子用：合并 quant_system OHLCV + 本地 amount 缓存 ============
# amount 由 fetch_amount.py 独立拉取（akshare 新浪日线端点返回 amount，quant_system
# 的 _normalize 丢弃了它）。VWAP = amount / volume 精确反推（非典型价近似）。
# amount 缓存目录 data_amt/ 独立于 quant_system/data/cache，绝不写其缓存。
AMT_DIR = QUANT_ROOT.parent / "survey" / "gtja191_port" / "data_amt"


def load_daily_with_vwap(symbol: str, adjust: str = "qfq") -> pd.DataFrame | None:
    """读 OHLCV（quant_system 缓存）+ amount（本地 data_amt），按 date 合并，加 vwap 列。
    返回 df[date,open,high,low,close,volume,amount,vwap] 升序，或 None（缺 OHLCV 或 amount）。
    """
    df = load_daily(symbol, adjust)
    if df is None or df.empty:
        return None
    p = AMT_DIR / f"stock_{symbol}_{adjust}_{DEFAULT_START}.parquet"
    if not p.exists():
        return None
    try:
        amt = pd.read_parquet(p)
    except Exception:
        return None
    if amt.empty or "amount" not in amt.columns:
        return None
    amt = amt[["date", "amount"]].copy()
    amt["date"] = pd.to_datetime(amt["date"])
    df = df.merge(amt, on="date", how="left")
    # vwap = amount / volume；volume=0 行已由 quant_system 丢弃，这里兜底防除零
    df["vwap"] = df["amount"] / df["volume"].replace(0, np.nan)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_batch_daily_with_vwap(symbols: list[str], adjust: str = "qfq") -> dict[str, pd.DataFrame]:
    """批量读 OHLCV+amount+vwap，缺失自动跳过。"""
    import numpy as np
    out = {}
    for s in symbols:
        df = load_daily_with_vwap(s, adjust)
        if df is not None and not df.empty:
            out[s] = df
    return out


# ============ 指数因子用：合并 OHLCV+amount+vwap + 市场指数 open/close ============
# 指数缓存复用 quant_system 的 index_real_{universe}.parquet（中证1000对应 csi1000），
# 只读不写。指数因子 #75/149/181/182 需 index_open/index_close（市场 beta/共动口径）。
_INDEX_CACHE: pd.DataFrame | None = None


def load_index_daily(universe: str = "csi1000") -> pd.DataFrame | None:
    """读指数日线缓存 index_real_{universe}.parquet，返回 df[date,open,high,low,close,volume] 升序。"""
    global _INDEX_CACHE
    if _INDEX_CACHE is not None:
        return _INDEX_CACHE
    p = CACHE_DIR / f"index_real_{universe}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    _INDEX_CACHE = df
    return df


def load_daily_with_vwap_index(symbol: str, adjust: str = "qfq", universe: str = "csi1000") -> pd.DataFrame | None:
    """读 OHLCV+amount+vwap+index_open+index_close，按 date 合并指数。
    返回 df[date,open,high,low,close,volume,amount,vwap,index_open,index_close] 升序，或 None。"""
    df = load_daily_with_vwap(symbol, adjust)
    if df is None or df.empty:
        return None
    idx = load_index_daily(universe)
    if idx is None:
        return None
    idx2 = idx[["date", "open", "close"]].rename(columns={"open": "index_open", "close": "index_close"})
    df = df.merge(idx2, on="date", how="left")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_batch_daily_with_vwap_index(symbols: list[str], adjust: str = "qfq", universe: str = "csi1000") -> dict[str, pd.DataFrame]:
    """批量读 OHLCV+amount+vwap+index，缺失自动跳过。"""
    out = {}
    for s in symbols:
        df = load_daily_with_vwap_index(s, adjust, universe)
        if df is not None and not df.empty:
            out[s] = df
    return out


if __name__ == "__main__":
    # 自测
    syms = load_constituents("csi1000")
    print(f"csi1000 成分股: {len(syms)} 只")
    got = load_batch_daily(syms[:5])
    for s, df in got.items():
        print(f"  {s}: {len(df)} 行 {df['date'].min().date()}→{df['date'].max().date()} cols={list(df.columns)}")
    print(f"前5只缓存命中: {len(got)}/5")
