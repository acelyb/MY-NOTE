"""
GTJA191 Alpha131 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK(DELAY(VWAP,1)))^TSRANK(CORR(CLOSE,MEAN(VOL,50),18),18)
DolphinDB:
  def gtjaAlpha131(close, vol, vwap){
      return pow(rowRank(vwap - mfirst(vwap,2), percent=true), mrank(mcorr(close, mavg(vol,50), 18), true, 18))
  }

翻译要点:
- 底：vwap-mfirst(vwap,2)=1日VWAP变化（研报 DELAY(VWAP,1) 在 RANK 内即 VWAP-前1日）；rowRank 排名（∈(0,1)）。
- 指数：mavg(vol,50)=50日量均；mcorr(close, 量均, 18)=18日相关；mrank(...,true,18)=18日升序排名。
- pow(底, 指数) 逐元素幂。长链50+18。

语义: VWAP 1日变化排名，以收盘-长均量18日相关的18日排名为幂。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, ts_corr, ts_mean, mrank, seq_pow


class Alpha131Factor(FactorBase):
    name = "gtja_alpha131"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 68:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        base = (vwap - mfirst(vwap, 2)).rolling(18, min_periods=1).rank(pct=True)
        c18 = ts_corr(close, ts_mean(vol, 50), 18)
        exp = mrank(c18, True, 18)
        val = seq_pow(base, exp).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
