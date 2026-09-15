"""
GTJA191 Alpha20 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100
DolphinDB:
  def gtjaAlpha20(close){
      return (close - mfirst(close, 7)) \ mfirst(close, 7) * 100
  }

翻译要点:
- mfirst(close,7)=DELAY(close,6)=delay(close,6)。
- 即6日收盘收益率×100（百分比形式）。
- 除零：6日前收盘为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 6日收盘收益率（%）。属价格动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay


class Alpha20Factor(FactorBase):
    name = "gtja_alpha20"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # delay(6)+1
            return None
        close = df["close"]
        d6 = delay(close, 6).replace(0, np.nan)
        val = ((close - d6) / d6 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
