"""
GTJA191 Alpha31 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-MEAN(CLOSE,12))/MEAN(CLOSE,12)*100
DolphinDB:
  def gtjaAlpha31(close){
      return (close - mavg(close, 12)) \ mavg(close, 12) * 100
  }

翻译要点:
- mavg(close,12)=ts_mean(close,12)。
- 即收盘相对12日均线的偏离率×100（%）。
- 除零：12日均值 为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 收盘相对12日均线的偏离率（%）。正值→价格在均线之上；负值→之下。
  属均线偏离/反转因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_mean


class Alpha31Factor(FactorBase):
    name = "gtja_alpha31"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 12:  # mean(12)
            return None
        close = df["close"]
        mean12 = ts_mean(close, 12).replace(0, np.nan)
        val = ((close - mean12) / mean12 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
