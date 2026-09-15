"""
GTJA191 Alpha134 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME
DolphinDB:
  def gtjaAlpha134(close, vol){
      return (close - mfirst(close, 13)) \ mfirst(close, 13) * vol
  }

翻译要点:
- mfirst(close,13)=delay(close,12)=12日前收盘。
- 12日收益率 × 当日成交量。
- 除零：12日前收盘为 0 时置 NaN。

语义: 12日收益率乘成交量。放量+大涨→因子大→预期未来收益高（量价动量），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha134Factor(FactorBase):
    name = "gtja_alpha134"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # delay(close,12)
            return None
        close, vol = df["close"], df["volume"]
        c12 = close.shift(12)   # DELAY(CLOSE,12)
        val = ((close - c12) / c12.replace(0, np.nan) * vol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
