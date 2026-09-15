"""
GTJA191 Alpha29 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*VOLUME
DolphinDB:
  def gtjaAlpha29(close, vol){
      return (close - mfirst(close, 7)) \ mfirst(close, 7) * vol
  }

翻译要点:
- mfirst(close,7)=delay(close,7)=DELAY(close,6)。
- 即6日收盘收益率 × 当日成交量（量加权动量）。
- 除零：6日前收盘为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 6日收益 × 当日量。放量上涨→大正值；放量下跌→大负值。量价动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay


class Alpha29Factor(FactorBase):
    name = "gtja_alpha29"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # delay(6)+1
            return None
        close, vol = df["close"], df["volume"]
        d6 = delay(close, 6).replace(0, np.nan)
        val = ((close - d6) / d6 * vol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
