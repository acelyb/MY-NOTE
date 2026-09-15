"""
GTJA191 Alpha15 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: OPEN/DELAY(CLOSE,1)-1
DolphinDB:
  def gtjaAlpha15(open, close){
      return open \ mfirst(close, 2) - 1
  }

翻译要点:
- DolphinDB `\` 为除法；mfirst(close,2)=DELAY(close,1)=delay(close,1)。
- 即当日开盘相对前一日收盘的跳空收益率（隔夜跳空）。
- 除零：前一日收盘为0用 replace(0,np.nan) 规避 inf。

语义: 隔夜跳空收益。开盘高于前收（正跳空）→ 值为正。
  隔夜信息反应，常作情绪/缺口因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay


class Alpha15Factor(FactorBase):
    name = "gtja_alpha15"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:  # delay(1)+1
            return None
        open_, close = df["open"], df["close"]
        prev_close = delay(close, 1).replace(0, np.nan)
        val = (open_ / prev_close - 1).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
