"""
GTJA191 Alpha175 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),6)
DolphinDB:
  def gtjaAlpha175(close, high, low){
      return mavg(max(max(high - low, abs(mfirst(close, 2) - high)), abs(mfirst(close, 2) - low)), 6)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘。
- TR = MAX(日内振幅, 跳空高-前收绝对值, 前收-低绝对值) = 真实波幅(True Range)。
- mavg(TR,6)=6日真实波幅均值 = ATR(6)。
- 与 alpha161(窗口12) 同结构，仅窗口不同。
- 最长链 delay(1)+mavg(6)=7 行起算。

语义: 6日平均真实波幅(ATR)。波动越大→因子越大，波动率维度，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha175Factor(FactorBase):
    name = "gtja_alpha175"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # delay(1) + mavg(6)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        dc1 = close.shift(1)    # DELAY(CLOSE,1)
        tr = np.maximum(np.maximum(high - low, (dc1 - high).abs()), (dc1 - low).abs())
        tr_s = pd.Series(tr, index=df.index)
        val = tr_s.rolling(6).mean().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
