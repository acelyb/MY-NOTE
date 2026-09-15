"""
GTJA191 Alpha8 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(DELTA(((((HIGH+LOW)/2)*0.2)+(VWAP*0.8)),4) * -1)
DolphinDB:
  def gtjaAlpha8(high, low, vwap){
      tmp = (high+low)\2*0.2 + vwap*0.8
      return rowRank((tmp - mfirst(tmp,5)) * (-1), percent=true)
  }

翻译要点:
- tmp = (H+L)/2*0.2 + VWAP*0.8 = 典型价与 VWAP 的加权混合（VWAP 主导）。
- mfirst(tmp,5)=delay(tmp,4)；tmp-mfirst(tmp,5)=DELTA(tmp,4)。
- 整体取负后做 rowRank → rolling pct rank 近似。

语义: (典型价×0.2+VWAP×0.8) 的4日变化的负排名。取负=反转口径。横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst


class Alpha8Factor(FactorBase):
    name = "gtja_alpha8"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:
            return None
        high, low, vwap = df["high"], df["low"], df["vwap"]
        tmp = (high + low) / 2 * 0.2 + vwap * 0.8
        delta4 = tmp - mfirst(tmp, 5)
        val = (delta4 * (-1)).rolling(5, min_periods=1).rank(pct=True).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
