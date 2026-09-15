"""
GTJA191 Alpha122 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)
    - DELAY(SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2),1))
  / DELAY(SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2),1)
DolphinDB:
  def gtjaAlpha122(close){
      A = ewmMean(ewmMean(ewmMean(log(close),alpha=2\13),alpha=2\13),alpha=2\13)
      return (A - move(A,1)) \ move(A,1)
  }

翻译要点:
- A = SMA(SMA(SMA(log(close),13,2),13,2),13,2) = 对 log(close) 做三次 ewmMean(alpha=2/13)。
- move(A,1)=delay(A,1)。(A - A_{t-1})/A_{t-1} = A 的日收益率。
- 分母 A_{t-1}=0 时除零置 NaN；log(close) 要求 close>0（日线收盘价通常>0）。

语义: 三重指数平滑对数收盘价的日收益率。平滑趋势的动量。
  上涨→因子正→预期未来收益高（趋势跟随）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ema_mean


class Alpha122Factor(FactorBase):
    name = "gtja_alpha122"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:  # ewm 递归
            return None
        close = df["close"]
        lc = np.log(close)
        A = ema_mean(ema_mean(ema_mean(lc, 2 / 13), 2 / 13), 2 / 13)
        A_prev = A.shift(1)   # DELAY(A,1)
        val = ((A - A_prev) / A_prev.replace(0, np.nan)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
