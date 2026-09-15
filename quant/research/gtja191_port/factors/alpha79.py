"""
GTJA191 Alpha79 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100
DolphinDB:
  def gtjaAlpha79(close){
      A = max((close - move(close,1)),0)
      B = abs(close - move(close,1))
      return ewmMean(A,alpha=1\12) \ ewmMean(B,alpha=1\12) * 100
  }

翻译要点:
- 与 alpha63（窗口6）、alpha67（窗口24）同源，窗口12。
- A=正向涨幅（下跌日记0）；B=绝对涨跌幅。
- SMA(A,12,1)=ewmMean(alpha=1/12)；SMA(B,12,1)=ewmMean(alpha=1/12)。
- 比值×100 = 12日指数平滑 RSI。
- 分母为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 12日指数平滑 RSI。介于 alpha63(6日) 和 alpha67(24日) 之间。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha79Factor(FactorBase):
    name = "gtja_alpha79"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # move(1) + ewm(需至少1个有效值)
            return None
        close = df["close"]
        chg = close - close.shift(1)
        A = chg.clip(lower=0)
        B = chg.abs()
        sma_a = sma_recursive(A, 12, 1)
        sma_b = sma_recursive(B, 12, 1)
        val = (sma_a / sma_b.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
