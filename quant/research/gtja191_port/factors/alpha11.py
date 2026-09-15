"""
GTJA191 Alpha11 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)*VOLUME, 6)
DolphinDB:
  def gtjaAlpha11(close, high, low, vol){
      return msum((close - low - (high - close)) \ (high - low) * vol, 6)
  }

翻译要点:
- (CLOSE-LOW)-(HIGH-CLOSE) = 2*CLOSE - HIGH - LOW = 收盘相对日内中点的偏离×2。
- 除以 (HIGH-LOW) 归一到 [-1,1]：收盘接近最高→+1，接近最低→-1。
- 乘以 VOLUME → 收盘位置×当日量。
- 过去6日累加。
- 分母 HIGH-LOW=0（一字板/停牌）时需保护，替换为 nan。
- 无横截面算子，单标的可忠实还原。

语义: 6日内"收盘强势度"×量的累加——收在高位且放量=多头主导，累加看多空力量。
  与 alpha84(OBV 带符号量) 不同：alpha84 用价涨跌方向定符号，alpha11 用收盘在日内位置定强度。
  是"日内收盘动能×量"的累积，更细粒度的量价共振。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha11Factor(FactorBase):
    name = "gtja_alpha11"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # sum(6)
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        rng = (high - low).replace(0, np.nan)
        pos = (close - low - (high - close)) / rng  # 收盘日内位置∈[-1,1]
        val = (pos * vol).rolling(6).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
