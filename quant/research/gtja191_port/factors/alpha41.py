"""
GTJA191 Alpha41 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(MAX(VWAP-DELAY(VWAP,3),5)) * -1
DolphinDB:
  def gtjaAlpha41(vwap){
      return rowRank(mmax(vwap - mfirst(vwap,4), 5), percent=true) * (-1)
  }

翻译要点:
- mfirst(vwap,4)=delay(vwap,3)=DELAY(VWAP,3)；vwap-前3日VWAP=3日VWAP变化。
- mmax(…,5)=过去5日该变化的最大值；rowRank 排名；取负。

语义: VWAP 3日变化的5日最大值排名，取负（反转）。横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_max, mfirst


class Alpha41Factor(FactorBase):
    name = "gtja_alpha41"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:
            return None
        vwap = df["vwap"]
        d = vwap - mfirst(vwap, 4)
        val = (ts_max(d, 5).rolling(5, min_periods=1).rank(pct=True) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
