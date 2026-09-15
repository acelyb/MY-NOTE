"""
GTJA191 Alpha59 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM((CLOSE=DELAY(CLOSE,1) ? 0 : CLOSE - (CLOSE>DELAY(CLOSE,1) ? MIN(LOW, DELAY(CLOSE,1)) : MAX(HIGH, DELAY(CLOSE,1)))), 20)
DolphinDB:
  def gtjaAlpha59(close, high, low){
      return msum(iif(close == mfirst(close, 2), 0,
                     close - iif(close > mfirst(close, 2), min(low, mfirst(close, 2)),
                                                      max(high, mfirst(close, 2)))), 20)
  }

翻译要点:
- mfirst(close,2)=昨收 C1。
- 持平(C==C1) 取0；
  上涨(C>C1) 取 C - MIN(LOW, C1) = 收盘相对"当日低点与昨收较高者"的突破幅度（正）；
  下跌(C<C1) 取 C - MAX(HIGH, C1) = 收盘相对"当日高点与昨收较低者"的跌幅（负）。
- 20日求和 → 累积净"收盘相对昨收的突破方向幅度"。
- 无横截面算子，单标的可忠实还原。

语义: 20日累积"收盘突破昨收的方向性幅度"。上涨日计正向突破，下跌日计负向跌幅，持平记0。
  类似累积动量，但用"相对昨收+当H/L"的突破定义。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha59Factor(FactorBase):
    name = "gtja_alpha59"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mfirst(2) + msum(20)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        c1 = close.shift(1)
        eq = (close == c1)
        up = (close > c1)
        # 上涨: close - min(low, c1)；下跌: close - max(high, c1)
        term_up = close - np.minimum(low, c1)
        term_dn = close - np.maximum(high, c1)
        term = pd.Series(np.where(eq.values, 0.0,
                                  np.where(up.values, term_up.values, term_dn.values)),
                         index=close.index)
        val = term.rolling(20).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
