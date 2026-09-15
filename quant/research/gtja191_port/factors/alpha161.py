"""
GTJA191 Alpha161 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),12)
DolphinDB:
  def gtjaAlpha161(close, high, low){
      return mavg(max(max(high - low, abs(mfirst(close, 2) - high)), abs(mfirst(close, 2) - low)), 12)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘。
- TR = MAX(日内振幅, 跳空高-前收绝对值, 前收-低绝对值) = 真实波幅(True Range)。
- mavg(TR,12)=12日真实波幅均值 = ATR(12)。
- 最长链 delay(1)+mavg(12)=13 行起算。

语义: 12日平均真实波幅(ATR)。波动越大→因子越大，波动率维度，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha161Factor(FactorBase):
    name = "gtja_alpha161"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # delay(1) + mavg(12)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        dc1 = close.shift(1)    # DELAY(CLOSE,1)
        tr = np.maximum(np.maximum(high - low, (dc1 - high).abs()), (dc1 - low).abs())
        tr_s = pd.Series(tr, index=df.index)
        val = tr_s.rolling(12).mean().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
