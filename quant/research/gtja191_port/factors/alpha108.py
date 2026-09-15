"""
GTJA191 Alpha108 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK(HIGH-MIN(HIGH,2))^RANK(CORR(VWAP,MEAN(VOL,120),6))) * -1
DolphinDB:
  def gtjaAlpha108(high, vol, vwap){
      return pow(rowRank(high - min(high,2), percent=true), rowRank(mcorr(vwap, mavg(vol,120), 6), percent=true)) * (-1)
  }

翻译要点:
- high - min(high,2)=high - ts_min(high,2)（当日高价相对2日最低高出的幅度）。
- rowRank 排名（底，∈(0,1)）；mcorr(vwap, 120日量均, 6)=6日相关；rowRank 排名（指数）。
- pow(底, 指数) 逐元素幂；整体取负。长链120。

语义: 高价相对2日低点高出的排名，以 VWAP-长均量相关排名为幂，取负。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_min, ts_corr, ts_mean, seq_pow


class Alpha108Factor(FactorBase):
    name = "gtja_alpha108"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 126:
            return None
        high, vol, vwap = df["high"], df["volume"], df["vwap"]
        base = (high - ts_min(high, 2)).rolling(6, min_periods=1).rank(pct=True)
        c6 = ts_corr(vwap, ts_mean(vol, 120), 6)
        exp = c6.rolling(6, min_periods=1).rank(pct=True)
        val = (seq_pow(base, exp) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
