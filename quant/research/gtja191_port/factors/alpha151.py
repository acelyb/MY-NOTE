"""
GTJA191 Alpha151 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(CLOSE-DELAY(CLOSE,20),20,1)
DolphinDB:
  def gtjaAlpha151(close){
      A = close-move(close,20)
      return ewmMean(A,alpha=1\20)
  }

翻译要点:
- move(close,20)=delay(close,20)=20日前收盘。
- A = close-delay(close,20) = 20日收盘价差。
- SMA(A,20,1) = ewmMean(alpha=1/20) 递归指数加权均值。
- 最长链 delay(20) + ewm(理论上全历史，但需 ≥20 行)。

语义: 20日收盘价差的指数加权均值。价差为正且持续→因子大→预期未来收益高（中期动量平滑），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha151Factor(FactorBase):
    name = "gtja_alpha151"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(20) + ewm
            return None
        close = df["close"]
        A = close - close.shift(20)            # CLOSE-DELAY(CLOSE,20)
        val = sma_recursive(A, 20, 1).iloc[-1]  # SMA(A,20,1)
        if pd.isna(val):
            return None
        return float(val)
