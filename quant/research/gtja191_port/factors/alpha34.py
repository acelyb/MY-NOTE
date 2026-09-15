"""
GTJA191 Alpha34 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(CLOSE,12)/CLOSE
DolphinDB:
  def gtjaAlpha34(close){
      return mavg(close, 12) \ close
  }

翻译要点:
- mavg(close,12)=ts_mean(close,12)。
- 即12日均线 / 当日收盘（alpha31 偏离率的另一种归一）。
- 除零：当日收盘 为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 12日均线与收盘的比值。>1 均线在价格之上（价格偏低）；<1 均线在价格之下。
  属均线偏离因子，与 alpha31 互补，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_mean


class Alpha34Factor(FactorBase):
    name = "gtja_alpha34"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 12:  # mean(12)
            return None
        close = df["close"]
        mean12 = ts_mean(close, 12)
        close_safe = close.replace(0, np.nan)
        val = (mean12 / close_safe).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
