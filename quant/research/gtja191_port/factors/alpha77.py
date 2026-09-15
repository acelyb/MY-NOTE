"""
GTJA191 Alpha77 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MIN(RANK(AVG(((HIGH+LOW)/2)+HIGH-(VWAP+HIGH),20)), RANK(AVG(CORR((HIGH+LOW)/2,MEAN(VOL,40),3),6)))
DolphinDB:
  def gtjaAlpha77(high, low, vol, vwap){
      return min(rowRank(mavg((high+low)\2 + high - (vwap+high), 1..20), percent=true), rowRank(mavg(mcorr((high+low)\2, mavg(vol,40), 3), 1..6), percent=true))
  }

翻译要点:
- 第一项：(H+L)/2 + H - (VWAP+H) = (H+L)/2 - VWAP（H 抵消）= 典型价与VWAP偏离；
  mavg(...,1..20) 加权均；rowRank 排名。
- 第二项：mcorr((H+L)/2, 40日量均, 3)=3日典型价与长均量相关；mavg(...,1..6) 加权均；rowRank 排名。
- 两项取 min。长链40+3。

语义: 典型价-VWAP偏离平滑排名 与 典型价-长均量相关平滑排名的最小值。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mavg_weighted, ts_corr, ts_mean


class Alpha77Factor(FactorBase):
    name = "gtja_alpha77"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 46:
            return None
        high, low, vol, vwap = df["high"], df["low"], df["volume"], df["vwap"]
        mid = (high + low) / 2
        t1 = mavg_weighted(mid - vwap, list(range(1, 21))).rolling(20, min_periods=1).rank(pct=True)
        c3 = ts_corr(mid, ts_mean(vol, 40), 3)
        t2 = mavg_weighted(c3, list(range(1, 7))).rolling(6, min_periods=1).rank(pct=True)
        val = pd.concat([t1, t2], axis=1).min(axis=1).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
