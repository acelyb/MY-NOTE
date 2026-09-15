"""
GTJA191 Alpha126 —— 移植自 DolphinDB gtja191Alpha.dos（研报标 stateless）。

研报公式: (CLOSE+HIGH+LOW)/3
DolphinDB:
  def gtjaAlpha126(close, high, low){
      return (close + high + low) \ 3
  }

翻译要点:
- 无窗口，直接当日 (close+high+low)/3 = 典型价格( Typical Price )。

语义: 当日典型价格。价高→因子大，方向以 IC 实测定（通常为动量/价格水平）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha126Factor(FactorBase):
    name = "gtja_alpha126"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 1:
            return None
        close, high, low = df["close"], df["high"], df["low"]
        val = ((close + high + low) / 3).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
