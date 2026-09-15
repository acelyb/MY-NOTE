"""
GTJA191 Alpha124 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-VWAP) / AVG(RANK(MAX(CLOSE,30),2))
DolphinDB:
  def gtjaAlpha124(close, vwap){
      return (close - vwap) \ mavg(rowRank(mmax(close,30), percent=true), 1..2)
  }

翻译要点:
- close-vwap=收盘-VWAP偏离（alpha120 的负向，正=收盘高于均价/尾盘拉升）。
- mmax(close,30)=30日最高收盘；rowRank 排名；mavg(...,1..2) 加权均（2窗）。
- 分子 / 分母。分母排名∈(0,1) 不为0。

语义: 收盘-VWAP偏离 / 30日最高收盘排名的平滑。VWAP-CLOSE 偏离信号的标准化。
  rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_max, mavg_weighted


class Alpha124Factor(FactorBase):
    name = "gtja_alpha124"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 31:
            return None
        close, vwap = df["close"], df["vwap"]
        rmax = ts_max(close, 30).rolling(30, min_periods=1).rank(pct=True)
        denom = mavg_weighted(rmax, list(range(1, 3)))
        val = ((close - vwap) / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
