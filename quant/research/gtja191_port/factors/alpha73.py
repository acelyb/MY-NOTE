"""
GTJA191 Alpha73 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (TSRANK(AVG(AVG(CORR(CLOSE,VOL,10),16),4),5) - RANK(AVG(CORR(VWAP,MEAN(VOL,30),4),3))) * -1
DolphinDB:
  def gtjaAlpha73(close, vol, vwap){
      return (mrank(mavg(mavg(mcorr(close,vol,10),1..16),1..4), true, 5) - rowRank(mavg(mcorr(vwap, mavg(vol,30),4), 1..3), percent=true)) * (-1)
  }

翻译要点:
- 第一项：mcorr(close,vol,10)=10日量价相关；mavg(...,1..16) 再 mavg(...,1..4) 双层加权均；
  mrank(...,true,5)=5日升序排名（绝对位置）。
- 第二项：mavg(vol,30)=30日量均；mcorr(vwap, 量均, 4)=4日相关；mavg(...,1..3) 加权均；rowRank 排名。
- 两项相减后取负。

语义: 量价相关双层平滑的5日排名 - VWAP-长均量相关平滑排名，取负。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, mavg_weighted, ts_mean, mrank


class Alpha73Factor(FactorBase):
    name = "gtja_alpha73"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 30:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        c10 = ts_corr(close, vol, 10)
        a1 = mavg_weighted(c10, list(range(1, 17)))
        a2 = mavg_weighted(a1, list(range(1, 5)))
        r1 = mrank(a2, True, 5)
        c4 = ts_corr(vwap, ts_mean(vol, 30), 4)
        r2 = mavg_weighted(c4, list(range(1, 4))).rolling(3, min_periods=1).rank(pct=True)
        val = ((r1 - r2) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
