"""
GTJA191 Alpha46 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/(4*CLOSE)
DolphinDB:
  def gtjaAlpha46(close){
      return (mavg(close, 3) + mavg(close, 6) + mavg(close, 12) + mavg(close, 24)) \ (4 * close)
  }

翻译要点:
- mavg(close,n)=ts_mean(close,n)。
- 多周期均线（3/6/12/24日）之和 ÷ (4×当日收盘)。
- 除零：当日收盘为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 多周期均线平均与收盘的比值。>1 多周期均线在价格之上（价格偏低/超卖）；
  <1 均线在价格之下（价格偏高/超买）。属均线偏离因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_mean


class Alpha46Factor(FactorBase):
    name = "gtja_alpha46"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # 最长均线 24
            return None
        close = df["close"]
        m3 = ts_mean(close, 3)
        m6 = ts_mean(close, 6)
        m12 = ts_mean(close, 12)
        m24 = ts_mean(close, 24)
        close_safe = close.replace(0, np.nan)
        val = ((m3 + m6 + m12 + m24) / (4 * close_safe)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
