"""
GTJA191 Alpha14 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: CLOSE-DELAY(CLOSE,5)
DolphinDB:
  def gtjaAlpha14(close){
      return close - mfirst(close, 6)
  }

翻译要点:
- mfirst(close,6)=DELAY(close,5)=delay(close,5)（mfirst(x,n)=delay(x,n-1)）。
- 即 DELTA(close,5)，当日收盘相对5日前收盘的变化量。
- 无横截面/排名算子，单标的可忠实还原。

语义: 5日收盘动量（价格变化量）。值为正→近期上涨，预期延续（动量）；
  值为负→近期下跌。属纯价格动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, delay


class Alpha14Factor(FactorBase):
    name = "gtja_alpha14"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # delay(5)+1
            return None
        close = df["close"]
        val = (close - delay(close, 5)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
