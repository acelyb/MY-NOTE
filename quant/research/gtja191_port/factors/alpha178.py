"""
GTJA191 Alpha178 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME
DolphinDB:
  def gtjaAlpha178(close, vol){
      return (close - mfirst(close, 2)) \ mfirst(close, 2) * vol
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘。
- 日收益率 × 当日成交量 = 量价动量。
- 除零：前日收盘为 0 时置 NaN。
- 与 alpha134(12日版) 同结构，窗口为1日。
- 需 delay(1) = 2 行起算。

语义: 日收益率乘成交量。放量+涨→因子大→预期未来收益高（量价动量），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha178Factor(FactorBase):
    name = "gtja_alpha178"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:  # delay(close,1)
            return None
        close, vol = df["close"], df["volume"]
        dc1 = close.shift(1)
        val = ((close - dc1) / dc1.replace(0, np.nan) * vol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
