"""
GTJA191 Alpha179 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(CORR(VWAP,VOL,4)) * RANK(CORR(RANK(LOW),RANK(MEAN(VOL,50)),12))
DolphinDB:
  def gtjaAlpha179(low, vol, vwap){
      return rowRank(mcorr(vwap, vol, 4), percent=true) * rowRank(mcorr(rowRank(low,percent=true), rowRank(mavg(vol,50),percent=true), 12), percent=true)
  }

翻译要点:
- 第一项：mcorr(vwap, vol, 4)=4日 VWAP-量时序相关；rowRank 排名。
- 第二项：rowRank(low)/rowRank(mavg(vol,50)) 排名；mcorr(...,12)=12日相关；rowRank 排名。
- 两项相乘。长链50。

语义: VWAP-量4日相关排名 × 低价-长均量12日相关排名。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_mean


class Alpha179Factor(FactorBase):
    name = "gtja_alpha179"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 62:
            return None
        low, vol, vwap = df["low"], df["volume"], df["vwap"]
        c1 = ts_corr(vwap, vol, 4)
        r1 = c1.rolling(12, min_periods=1).rank(pct=True)
        rl = low.rolling(12, min_periods=1).rank(pct=True)
        rv = ts_mean(vol, 50).rolling(50, min_periods=1).rank(pct=True)
        c2 = ts_corr(rl, rv, 12)
        r2 = c2.rolling(12, min_periods=1).rank(pct=True)
        val = (r1 * r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
