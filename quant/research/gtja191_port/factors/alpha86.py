"""
GTJA191 Alpha86 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (0.25 < ((DELAY(CLOSE,20)-DELAY(CLOSE,10))/10 - (DELAY(CLOSE,10)-CLOSE)/10))
    ? -1
    : ((((DELAY(CLOSE,20)-DELAY(CLOSE,10))/10 - (DELAY(CLOSE,10)-CLOSE)/10) < 0)
        ? 1
        : (-1 * (CLOSE - DELAY(CLOSE,1))))
DolphinDB:
  def gtjaAlpha86(close){
      cond1 = (0.25 < ((mfirst(close, 21) - mfirst(close, 11)) \ 10 - (mfirst(close, 11) - close) \ 10))
      cond2 = (((mfirst(close, 21) - mfirst(close, 11)) \ 10 - (mfirst(close, 11) - close) \ 10) < 0)
      iffalse = iif(cond2, 1, -1 * 1 * (close - mfirst(close, 2)))
      return iif(cond1, -1 * 1, iffalse)
  }

翻译要点:
- mfirst(close,21)=delay(close,20)；mfirst(close,11)=delay(close,10)；mfirst(close,2)=delay(close,1)。
- 记 g = (close_{t-20}-close_{t-10})/10 - (close_{t-10}-close_t)/10 = 近10日相比前10日的斜率变化。
- 分段: g>0.25 → -1；g<0 → 1；0<=g<=0.25 → -(close-close_{t-1})。
- iif(cond,a,b)=np.where；返回标量末位。

语义: 价格加速度分段因子。近10日动量大幅加速(>0.25)→-1(看空)；
  动量反转(g<0)→1(看多)；温和加速(0~0.25)→负的当日涨幅(反转)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha86Factor(FactorBase):
    name = "gtja_alpha86"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(close,20)
            return None
        close = df["close"]
        c20 = close.shift(20)   # DELAY(CLOSE,20)
        c10 = close.shift(10)   # DELAY(CLOSE,10)
        c1 = close.shift(1)     # DELAY(CLOSE,1)
        g = (c20 - c10) / 10 - (c10 - close) / 10
        val = np.where(g > 0.25, -1.0,
                       np.where(g < 0, 1.0, -1.0 * (close - c1)))
        val = pd.Series(val, index=close.index).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
