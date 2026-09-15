"""
GTJA191 Alpha130 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(AVG(CORR((HIGH+LOW)/2,MEAN(VOL,40),9),10)) / RANK(AVG(CORR(RANK(VWAP),RANK(VOL),7),3))
DolphinDB:
  def gtjaAlpha130(high, low, vol, vwap){
      return rowRank(mavg(mcorr((high+low)\2, mavg(vol,40), 9), 1..10), percent=true) \ rowRank(mavg(mcorr(rowRank(vwap,percent=true), rowRank(vol,percent=true), 7), 1..3), percent=true)
  }

翻译要点:
- 分子：(H+L)/2 典型价；mavg(vol,40)=40日量均；mcorr(...,9)=9日相关；mavg(...,1..10) 加权均；rowRank 排名。
- 分母：rowRank(vwap)/rowRank(vol) 排名；mcorr(...,7)=7日相关；mavg(...,1..3) 加权均；rowRank 排名。
- 分子 / 分母。长链40+9。

语义: 典型价-长均量9日相关平滑排名 / VWAP-量排名7日相关平滑排名。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_mean, mavg_weighted


class Alpha130Factor(FactorBase):
    name = "gtja_alpha130"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 50:
            return None
        high, low, vol, vwap = df["high"], df["low"], df["volume"], df["vwap"]
        mid = (high + low) / 2
        c1 = ts_corr(mid, ts_mean(vol, 40), 9)
        num = mavg_weighted(c1, list(range(1, 11))).rolling(10, min_periods=1).rank(pct=True)
        rvw = vwap.rolling(7, min_periods=1).rank(pct=True)
        rv = vol.rolling(7, min_periods=1).rank(pct=True)
        c2 = ts_corr(rvw, rv, 7)
        den = mavg_weighted(c2, list(range(1, 4))).rolling(3, min_periods=1).rank(pct=True)
        val = (num / den).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
