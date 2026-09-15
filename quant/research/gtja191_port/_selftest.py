"""自测框架：读 csi1000 缓存 + 用一个 momentum 因子验证 IC 口径。

预期：momentum_20 在 csi1000 月频应稳定反向（memory 记录 IC≈-0.053），
若我的独立框架跑出同量级负 IC，说明 cache_reader + ic.py 口径正确。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from base import FactorBase
from cache_reader import load_constituents, load_batch_daily
from ic import calc_factor_ic, ic_summary, interpret


class Momentum(FactorBase):
    name = "momentum_20"

    def calc(self, df: pd.DataFrame) -> float | None:
        n = 20
        if len(df) < n + 1:
            return None
        return df["close"].iloc[-1] / df["close"].iloc[-n - 1] - 1


if __name__ == "__main__":
    syms = load_constituents("csi1000")
    print(f"csi1000 成分股: {len(syms)} 只, 读缓存...")
    pdfs = load_batch_daily(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}")

    # 看 date 范围
    dr = sorted(set().union(*[set(d["date"]) for d in pdfs.values()]))
    print(f"合并日期轴: {len(dr)} 天, {pd.Timestamp(dr[0]).date()} → {pd.Timestamp(dr[-1]).date()}")

    print("\n跑 momentum_20 IC (horizon=21, freq=21, 月频)...")
    ic = calc_factor_ic(pdfs, Momentum(), horizon=21, freq=21)
    s = ic_summary(ic["ic"] if not ic.empty else pd.Series(dtype=float))
    print(f"  IC均值={s['ic_mean']:+.4f}  ICIR={s['icir']:+.3f}  胜率={s['win_rate']:.1%}  t={s['t_stat']:+.2f}  n={s['n']}")
    print(f"  判断: {interpret(s)}")
    print("\n预期对照: memory 记录 csi1000 momentum 月频 IC≈-0.053 反向。若量级/方向吻合则框架口径正确。")
