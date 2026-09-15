"""
GTJA191 Alpha61 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(RANK(DELAY(VWAP-DELAY(VWAP,1),12)), RANK(CORR(LOW,SUM(AVG(VOL,80),8),17))) * -1
DolphinDB:
  def gtjaAlpha61(low, vol, vwap){
      return (max(rowRank(mavg(vwap-mfirst(vwap,2), 1..12), percent=true), rowRank(mavg(rowRank(mcorr(low, mavg(vol,80), 8), percent=true), 1..17), percent=true))) * (-1)
  }

翻译要点:
- 第一项：vwap-mfirst(vwap,2)=1日VWAP变化；mavg(...,1..12) 加权均；rowRank 排名。
- 第二项：mavg(vol,80)=80日量均；mcorr(low, 量均, 8)=8日低价与长均量相关；rowRank 排名后再 mavg(...,1..17) 加权均再排名。
- 两项取 max 后整体取负。
- 长链80+8+17。

语义: VWAP变化平滑排名与低价-量相关平滑排名的最大值，取负。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, mavg_weighted, ts_mean, ts_corr


class Alpha61Factor(FactorBase):
    name = "gtja_alpha61"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 105:
            return None
        low, vol, vwap = df["low"], df["volume"], df["vwap"]
        d = vwap - mfirst(vwap, 2)
        t1 = mavg_weighted(d, list(range(1, 13))).rolling(12, min_periods=1).rank(pct=True)
        corr8 = ts_corr(low, ts_mean(vol, 80), 8)
        rc = corr8.rolling(8, min_periods=1).rank(pct=True)
        t2 = mavg_weighted(rc, list(range(1, 18))).rolling(17, min_periods=1).rank(pct=True)
        val = (pd.concat([t1, t2], axis=1).max(axis=1) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
