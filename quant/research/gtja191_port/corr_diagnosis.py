"""
相关性诊断：看 GTJA191 显著因子与现有因子的两两截面相关性，
判断 alpha167/-0.0993 是 momentum 的"更好替代"还是"同信号变体"，
以及哪些是新维度（低相关=独立增量）。

方法：在若干采样点算各因子的截面值，求跨时点的平均两两 Spearman 相关。
只读缓存，不改 quant_system。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from cache_reader import load_constituents, load_batch_daily
from factors import (
    Alpha6Factor, Alpha47Factor, Alpha99Factor,
    Alpha135Factor, Alpha143Factor, Alpha167Factor,
)

# 现有因子复刻（与 quant_system 口径一致，单标的）
class Momentum20:
    name = "momentum_20"
    def calc_value(self, df):
        if len(df) < 21: return None
        return df["close"].iloc[-1] / df["close"].iloc[-21] - 1

class Reversal60:
    """现有 reversal：60日收益取负（跌越多因子越大）"""
    name = "reversal_60"
    def calc_value(self, df):
        if len(df) < 61: return None
        return -(df["close"].iloc[-1] / df["close"].iloc[-61] - 1)

class Amplitude:
    """现有 low_vol 口径的振幅（日内振幅 hi-lo/close，取负=低波动越大越好）"""
    name = "amplitude(low_vol口径)"
    def calc_value(self, df):
        if len(df) < 2: return None
        amp = (df["high"] - df["low"]) / df["close"]
        return -float(amp.iloc[-1])

FACTORS = {
    "alpha6": Alpha6Factor(),
    "alpha47": Alpha47Factor(),
    "alpha99": Alpha99Factor(),
    "alpha135": Alpha135Factor(),
    "alpha143": Alpha143Factor(),
    "alpha167": Alpha167Factor(),
    "momentum_20(现有)": Momentum20(),
    "reversal_60(现有)": Reversal60(),
    "amplitude(现有低波动)": Amplitude(),
}


def cross_section_values(pdfs, date, sym_data):
    """算某日所有因子的截面值 {factor_name: {sym: val}}。sym_data 已 set_index('date')。"""
    out = {}
    for fname, fac in FACTORS.items():
        vals = {}
        for s, d in sym_data.items():
            pos = int(np.searchsorted(d.index.values, np.datetime64(date)))
            if pos >= len(d) or d.index[pos] != date:
                continue
            v = fac.calc_value(d.iloc[:pos + 1])
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                vals[s] = v
        out[fname] = pd.Series(vals)
    return out


def main():
    syms = load_constituents("csi1000")
    print(f"csi1000: {len(syms)} 只, 读缓存...")
    pdfs = load_batch_daily(syms)
    sym_data = {s: df.set_index("date") for s, df in pdfs.items() if not df.empty}
    all_dates = sorted(set().union(*[set(d.index) for d in sym_data.values()]))
    # 月频采样点（与 IC 一致，留出 horizon=21 尾部）
    dates = all_dates[:-21:21]
    print(f"采样 {len(dates)} 个时点算截面相关性...")

    # 累积各时点的截面值，算平均两两 Spearman
    corr_acc = pd.DataFrame(index=list(FACTORS), columns=list(FACTORS), dtype=float)
    cnt = 0
    for date in dates:
        cs = cross_section_values(pdfs, date, sym_data)
        names = list(FACTORS)
        mat = pd.DataFrame({n: cs[n] for n in names})
        if mat.dropna(how="all").shape[0] < 10:
            continue
        c = mat.corr(method="spearman")
        corr_acc = corr_acc.add(c, fill_value=0)
        cnt += 1
    corr_mean = corr_acc / cnt

    print("\n=== 因子两两截面相关性（跨时点平均 Spearman）===")
    print(corr_mean.round(3).to_string())
    print("\n=== 关键对照（|corr|<0.3 视为独立新维度）===")
    for col in ["momentum_20(现有)", "reversal_60(现有)", "amplitude(现有低波动)"]:
        print(f"\n  vs {col}:")
        rel = corr_mean[col].drop(labels=[col]).sort_values(key=abs, ascending=False)
        for fname, c in rel.items():
            tag = "高相关(同信号变体?)" if abs(c) > 0.5 else ("中相关" if abs(c) > 0.3 else "低相关·独立增量")
            print(f"    {fname:<28} corr={c:+.3f}  {tag}")


if __name__ == "__main__":
    main()
