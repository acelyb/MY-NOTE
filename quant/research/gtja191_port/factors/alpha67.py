"""
GTJA191 Alpha67 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(MAX(CLOSE-DELAY(CLOSE,1),0),24,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),24,1)*100
DolphinDB:
  def gtjaAlpha67(close){
      A = max((close - move(close,1)),0)
      B = abs(close - move(close,1))
      return ewmMean(A,alpha=1\24) \ ewmMean(B,alpha=1\24) * 100
  }

翻译要点:
- 与 alpha63（窗口6）、alpha79（窗口12）同源，窗口24。
- A=正向涨幅（下跌日记0）；B=绝对涨跌幅。
- SMA(A,24,1)=ewmMean(alpha=1/24)；SMA(B,24,1)=ewmMean(alpha=1/24)。
- 比值×100 = 24日指数平滑 RSI。
- 分母为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 24日指数平滑 RSI。比 alpha63(6日) 更慢，反映中期超买超卖。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha67Factor(FactorBase):
    name = "gtja_alpha67"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:  # move(1) + ewm(需至少1个有效值)
            return None
        close = df["close"]
        chg = close - close.shift(1)
        A = chg.clip(lower=0)
        B = chg.abs()
        sma_a = sma_recursive(A, 24, 1)
        sma_b = sma_recursive(B, 24, 1)
        val = (sma_a / sma_b.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
