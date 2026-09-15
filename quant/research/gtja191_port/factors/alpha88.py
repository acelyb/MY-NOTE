"""
GTJA191 Alpha88 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-DELAY(CLOSE,20))/DELAY(CLOSE,20)*100
DolphinDB:
  def gtjaAlpha88(close){
      return (close - mfirst(close, 21)) \ mfirst(close, 21) * 100
  }

翻译要点:
- mfirst(close,21)=delay(close,20)。
- 20日收益率(乘100)。close_{t-20}=0 时除零置 NaN。

语义: 20日收盘收益率(%)。动量类，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha88Factor(FactorBase):
    name = "gtja_alpha88"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(close,20)
            return None
        close = df["close"]
        c20 = close.shift(20)   # DELAY(CLOSE,20)
        val = ((close - c20) / c20.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
