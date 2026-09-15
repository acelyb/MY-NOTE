"""
GTJA191 Alpha90 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(CORR(RANK(VWAP),RANK(VOL),5)) * -1
DolphinDB:
  def gtjaAlpha90(vol, vwap){
      return rowRank(mcorr(rowRank(vwap,percent=true), rowRank(vol,percent=true), 5), percent=true) * (-1)
  }

翻译要点:
- rowRank(vwap)/rowRank(vol) 排名；mcorr(...,5)=5日时序相关；rowRank 排名；取负。

语义: VWAP-量排名的5日时序相关排名，取负。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr


class Alpha90Factor(FactorBase):
    name = "gtja_alpha90"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:
            return None
        vol, vwap = df["volume"], df["vwap"]
        rvw = vwap.rolling(5, min_periods=1).rank(pct=True)
        rv = vol.rolling(5, min_periods=1).rank(pct=True)
        c5 = ts_corr(rvw, rv, 5)
        val = (c5.rolling(5, min_periods=1).rank(pct=True) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
