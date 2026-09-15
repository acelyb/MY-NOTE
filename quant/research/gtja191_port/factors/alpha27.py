"""
GTJA191 Alpha27 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: WMA((CLOSE-DELAY(CLOSE,3))/DELAY(CLOSE,3)*100
             +(CLOSE-DELAY(CLOSE,6))/DELAY(CLOSE,6)*100, 12)
DolphinDB:
  def gtjaAlpha27(close){
      return mavg((close-move(close,3))\move(close,3)*100 + (close-move(close,6))\move(close,6)*100, 1..12 * 0.9, 12)
  }

翻译要点:
- move(close,3)=delay(close,3)；move(close,6)=delay(close,6)。
- A = 3日收益率×100 + 6日收益率×100（双周期动量之和）。
- mavg(A, 1..12*0.9, 12)=WMA(A,12)（0.9^i 权重的加权均，base.py wma 语义）。
  注：DolphinDB mavg(x, 1..n*0.9, n) 即 wma(x,n)（0.9^i 权重），与 base.py wma 一致。
- 除零：delay(close,3/6) 为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 3日与6日双周期收益率之和，经 WMA(0.9^i) 平滑。属多周期平滑动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay, wma


class Alpha27Factor(FactorBase):
    name = "gtja_alpha27"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 18:  # delay(6)+wma(12)
            return None
        close = df["close"]
        d3 = delay(close, 3).replace(0, np.nan)
        d6 = delay(close, 6).replace(0, np.nan)
        A = (close - d3) / d3 * 100 + (close - d6) / d6 * 100
        val = wma(A, 12).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
