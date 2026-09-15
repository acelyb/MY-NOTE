"""
IC 检验（独立实现，口径复刻 quant_system factors/ic.py 的 calc_factor_ic）。

核心：t 日因子值（截面）与 [t, t+horizon] 未来收益的 Spearman 秩相关 = Rank IC。
防未来函数：因子只用 ≤t 数据（d.iloc[:pos+1] 截断），收益用未来 horizon 日。
采样 freq 天去自相关。

与 quant_system ic.py 的等价点（已逐行核对）：
- _future_return: closes[t+n]/closes[t]-1
- 截面 spearmanr
- searchsorted 位置切片（numpy>=2.0 用 np.datetime64）
- 样本门槛 <10 不算
- ic_summary: IC均值/ICIR/胜率/t值

唯一差异：这里只做单因子 IC（不依赖 composite_score），独立无依赖。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from base import FactorBase


def _future_return(closes: pd.Series, idx: int, n: int) -> float | None:
    """idx 位置未来 n 日收益，数据不足或价格为 0 返回 None。"""
    if idx + n >= len(closes):
        return None
    c0, c1 = closes.iloc[idx], closes.iloc[idx + n]
    if c0 <= 0:
        return None
    return c1 / c0 - 1


def calc_factor_ic(price_dfs: dict[str, pd.DataFrame], factor: FactorBase,
                   horizon: int = 21, freq: int = 21) -> pd.DataFrame:
    """计算单因子 IC 序列。返回 DataFrame[date, ic]。"""
    all_dates = sorted(set().union(*[set(df["date"]) for df in price_dfs.values()]))
    sym_data = {s: df.set_index("date") for s, df in price_dfs.items() if not df.empty}

    records = []
    for i in range(0, len(all_dates) - horizon, freq):
        date = all_dates[i]
        factor_vals, future_rets = {}, {}
        for s, d in sym_data.items():
            pos = int(np.searchsorted(d.index.values, np.datetime64(date)))
            if pos >= len(d) or d.index[pos] != date:
                continue
            sub = d.iloc[:pos + 1]
            fv = factor.calc_value(sub)
            if fv is None or (isinstance(fv, float) and np.isnan(fv)):
                continue
            fr = _future_return(d["close"], pos, horizon)
            if fr is None:
                continue
            factor_vals[s] = fv
            future_rets[s] = fr

        if len(factor_vals) < 10:
            continue
        common = pd.Index(factor_vals.keys()).intersection(pd.Index(future_rets.keys()))
        if len(common) < 10:
            continue
        f_s = pd.Series(factor_vals).loc[common]
        r_s = pd.Series(future_rets).loc[common]
        ic, _ = spearmanr(f_s, r_s)
        if not np.isnan(ic):
            records.append({"date": date, "ic": ic})

    return pd.DataFrame(records).set_index("date") if records else pd.DataFrame(columns=["ic"])


def ic_summary(ic_series: pd.Series) -> dict:
    if ic_series.empty:
        return {"ic_mean": np.nan, "icir": np.nan, "win_rate": np.nan,
                "t_stat": np.nan, "n": 0}
    n = len(ic_series)
    ic_mean = ic_series.mean()
    ic_std = ic_series.std()
    icir = ic_mean / ic_std if ic_std > 0 else np.nan
    win_rate = (ic_series > 0).mean()
    t_stat = ic_mean / (ic_std / np.sqrt(n)) if ic_std > 0 else np.nan
    return {"ic_mean": ic_mean, "icir": icir, "win_rate": win_rate,
            "t_stat": t_stat, "n": n}


def interpret(s: dict) -> str:
    ic = s.get("ic_mean", np.nan)
    if np.isnan(ic):
        return "样本不足"
    strength = "弱" if abs(ic) < 0.03 else ("中" if abs(ic) < 0.05 else "强")
    stable = "稳定" if (not np.isnan(s["icir"]) and abs(s["icir"]) > 0.5) else "不稳定"
    sig = "显著" if (not np.isnan(s["t_stat"]) and abs(s["t_stat"]) > 2) else "不显著"
    direction = "正向" if ic > 0 else "反向"
    return f"{direction}·{strength}·{stable}·{sig}"
