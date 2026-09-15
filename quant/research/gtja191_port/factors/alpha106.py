"""
GTJA191 Alpha106 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: CLOSE-DELAY(CLOSE,20)
DolphinDB:
  def gtjaAlpha106(close){
      return close - mfirst(close, 21)
  }

翻译要点:
- mfirst(close,21)=delay(close,20)。20日收盘价差(绝对值)。

语义: 20日收盘价绝对变化。与 alpha88(20日收益率% ) 同族，
  alpha106 是价差绝对值而非收益率。动量类，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha106Factor(FactorBase):
    name = "gtja_alpha106"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(close,20)
            return None
        close = df["close"]
        val = (close - close.shift(20)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
