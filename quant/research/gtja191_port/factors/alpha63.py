"""
GTJA191 Alpha63 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(MAX(CLOSE-DELAY(CLOSE,1),0),6,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),6,1)*100
DolphinDB:
  def gtjaAlpha63(close){
      A = max((close - move(close,1)),0)
      B = abs(close - move(close,1))
      return ewmMean(A,alpha=1\6) \ ewmMean(B,alpha=1\6) * 100
  }

翻译要点:
- move(close,1)=delay(close,1)=昨收。
- A=MAX(C-C1, 0)=正向涨幅（下跌日记0）；B=|C-C1|=绝对涨跌幅。
- SMA(A,6,1)=ewmMean(alpha=1/6)；SMA(B,6,1)=ewmMean(alpha=1/6)。
- 比值×100 = RSI(6) 形式（6日指数平滑 RSI）。
- 与 alpha67（窗口24）、alpha79（窗口12）同源，窗口不同。
- 分母为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 6日指数平滑 RSI。高值=超买，低值=超卖。反转类用法 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha63Factor(FactorBase):
    name = "gtja_alpha63"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # move(1) + ewm(需至少1个有效值)
            return None
        close = df["close"]
        chg = close - close.shift(1)
        A = chg.clip(lower=0)
        B = chg.abs()
        sma_a = sma_recursive(A, 6, 1)
        sma_b = sma_recursive(B, 6, 1)
        val = (sma_a / sma_b.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
