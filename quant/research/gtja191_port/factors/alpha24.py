"""
GTJA191 Alpha24 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(CLOSE-DELAY(CLOSE,5),5,1)
DolphinDB:
  def gtjaAlpha24(close){
      A = close - move(close,5)
      return ewmMean(A,alpha=1\5)
  }

翻译要点:
- move(close,5)=delay(close,5)；A=5日收盘动量（delta(close,5)）。
- ewmMean(alpha=1/5)=ema_mean(A,1/5)=sma_recursive(A,5,1)（adjust=False 递归 EWM）。
- 即5日收盘动量的 EWM(1/5) 平滑值。
- 无横截面算子，单标的可忠实还原。

语义: 5日收盘动量经指数平滑。属平滑动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, delay, ema_mean


class Alpha24Factor(FactorBase):
    name = "gtja_alpha24"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # delay(5)+ewm
            return None
        close = df["close"]
        A = close - delay(close, 5)
        val = ema_mean(A, 1 / 5).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
