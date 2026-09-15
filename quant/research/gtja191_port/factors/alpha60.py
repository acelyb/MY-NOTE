"""
GTJA191 Alpha60 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME, 20)
DolphinDB:
  def gtjaAlpha60(close, high, low, vol){
      return msum((close - low - (high - close)) \ (high - low) * vol, 20)
  }

翻译要点:
- (CLOSE-LOW)-(HIGH-CLOSE) = 2*CLOSE - HIGH - LOW = 2*(CLOSE - (HIGH+LOW)/2)。
  即"收盘相对当日中枢的偏离"（正值=收在中枢之上）。
- 除以(HIGH-LOW)=当日振幅，归一化为[-1,1]；再乘成交量。
- 20日求和 → 累积"收盘位置×量"。
- 分母为0（一字板 H==L）时替换 nan 避免除零。
- 无横截面算子，单标的可忠实还原。

语义: 20日累积"收盘相对当日中枢的归一化偏离×成交量"。
  高值=收盘持续在中枢之上且放量（多方控盘）；低值=收盘在中枢之下放量。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha60Factor(FactorBase):
    name = "gtja_alpha60"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # msum(20)
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        spread = (high - low).replace(0, np.nan)
        term = ((close - low) - (high - close)) / spread * vol
        val = term.rolling(20).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
