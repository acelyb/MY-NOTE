"""
GTJA191 Alpha36 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(SUM(CORR(RANK(VOLUME),RANK(VWAP),6),2))
DolphinDB:
  def gtjaAlpha36(vol, vwap){
      return rowRank(msum(mcorr(rowRank(vol,percent=true), rowRank(vwap,percent=true), 6), 2), percent=true)
  }

翻译要点:
- rowRank(vol)/rowRank(vwap) → rolling pct rank 近似。
- mcorr(量排名, VWAP排名, 6) = 6日时序相关。
- msum(…,2) = 2日累加；外层 rowRank 排名。

语义: 量-VWAP 排名相关的6日时序相关的2日累加排名。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_sum


class Alpha36Factor(FactorBase):
    name = "gtja_alpha36"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 8:
            return None
        vol, vwap = df["volume"], df["vwap"]
        rv = vol.rolling(6, min_periods=1).rank(pct=True)
        rvw = vwap.rolling(6, min_periods=1).rank(pct=True)
        corr6 = ts_corr(rv, rvw, 6)
        val = ts_sum(corr6, 2).rolling(8, min_periods=1).rank(pct=True).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
