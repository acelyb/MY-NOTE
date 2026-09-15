"""
GTJA191 Alpha135 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(DELAY(CLOSE/DELAY(CLOSE,20),1), 20, 1)
DolphinDB:
  def gtjaAlpha135(close){
      A = move(close\\move(close,20),1)
      return ewmMean(A, alpha=1\\20)
  }

翻译要点:
- CLOSE/DELAY(CLOSE,20) = close_t / close_{t-20} —— 20日收益率（含1的累计涨幅比）
- DELAY(...,1) = shift(1) —— 整体延迟1日（防当日未来函数：用昨日算的20日涨幅）
- SMA(A,20,1)=研报递归指数加权 Y_t=(A_{t-1}*1+Y_{t-1}*19)/20，等价 EWM(alpha=1/20, adjust=False)

语义: 20日动量延迟1日后做长递归加权平滑——较慢的趋势因子。
方向: 20日涨幅越大→因子越大→动量逻辑（正向？）。IC 定夺，A股中长期常反转。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha135Factor(FactorBase):
    name = "gtja_alpha135"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 22:  # 需 20日 + delay1 + 平滑起步
            return None
        close = df["close"]
        ret20 = close / close.shift(20)  # CLOSE/DELAY(CLOSE,20)
        a = ret20.shift(1)               # DELAY(...,1)
        sma = sma_recursive(a, 20, 1)    # SMA(A,20,1)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
