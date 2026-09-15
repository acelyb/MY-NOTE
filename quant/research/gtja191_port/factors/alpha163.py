"""
GTJA191 Alpha163 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK((-1*RET)*MEAN(VOL,20)*VWAP*(HIGH-CLOSE))
DolphinDB:
  def gtjaAlpha163(close, high, vol, vwap){
      return rowRank(-1 * (ratios(close)-1) * mavg(vol,20) * vwap * (high-close), percent=true)
  }

翻译要点:
- ratios(close)-1=日收益率 ret。
- -ret × 20日均量 × VWAP × (high-close) = 负收益 × 流动性 × 均价 × 上影线强度的乘积。
- rowRank 排名。含横截面 rank 近似（有损）。

语义: 负收益、流动性、均价、上影线的联合强度排名（下跌+放量+上影=抛压信号）。
  rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ret, ts_mean


class Alpha163Factor(FactorBase):
    name = "gtja_alpha163"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        close, high, vol, vwap = df["close"], df["high"], df["volume"], df["vwap"]
        r = ret(close)
        val = (-1 * r * ts_mean(vol, 20) * vwap * (high - close)).rolling(20, min_periods=1).rank(pct=True).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
