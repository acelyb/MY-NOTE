"""
GTJA191 Alpha18 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: CLOSE/DELAY(CLOSE,5)
DolphinDB:
  def gtjaAlpha18(close){
      return close \ mfirst(close, 6)
  }

翻译要点:
- mfirst(close,6)=DELAY(close,5)=delay(close,5)。
- 即当日收盘 / 5日前收盘，5日价格相对比（非涨跌幅，是比值）。
- 除零：5日前收盘为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 5日价格比。>1 上涨，<1 下跌。与 alpha14(差值动量) 同源不同尺度（比值 vs 差值）。
  属价格动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay


class Alpha18Factor(FactorBase):
    name = "gtja_alpha18"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # delay(5)+1
            return None
        close = df["close"]
        prev = delay(close, 5).replace(0, np.nan)
        val = (close / prev).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
