"""
GTJA191 Alpha169 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SMA(MEAN(DELAY(SMA(CLOSE-DELAY(CLOSE,1),9,1),1),12)
      - MEAN(DELAY(SMA(CLOSE-DELAY(CLOSE,1),9,1),1),26), 10, 1)
DolphinDB:
  def gtjaAlpha169(close){
      A = close-move(close,1)
      B = ewmMean(A,alpha=1\9)
      C = mavg((move(B,1)),12) - mavg((move(B,1)),26)
      return ewmMean(C,alpha=1\10)
  }

翻译要点:
- move(close,1)=delay(close,1)=前日收盘；A=日涨跌。
- B = SMA(A,9,1) = ewmMean(alpha=1/9) 递归指数加权均值。
- move(B,1)=delay(B,1)；C = MEAN(delay(B,1),12) - MEAN(delay(B,1),26) = B 的12-26双均线差(MACD柱)。
- 结果 = SMA(C,10,1) = ewmMean(alpha=1/10)。
- 最长链：delay(1)+ewm(9 理论全历史)+delay(1)+mavg(26)+ewm(10) ≈ 37 行起算。

语义: 涨跌的SMA(9)的12-26双均线差再SMA(10)（嵌套MACD类动量，作用于价差非价比）。
      动量向上→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha169Factor(FactorBase):
    name = "gtja_alpha169"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 37:  # delay(1)+ewm(9)+delay(1)+mavg(26)+ewm(10)
            return None
        close = df["close"]
        A = close - close.shift(1)               # close-move(close,1)
        B = sma_recursive(A, 9, 1)               # ewmMean(alpha=1/9)
        dB = B.shift(1)                          # move(B,1)=delay(B,1)
        C = dB.rolling(12).mean() - dB.rolling(26).mean()
        val = sma_recursive(C, 10, 1).iloc[-1]   # ewmMean(alpha=1/10)
        if pd.isna(val):
            return None
        return float(val)
