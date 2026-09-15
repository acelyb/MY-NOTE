"""
GTJA191 Alpha68 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME, 15, 2)
DolphinDB:
  def gtjaAlpha68(high, low, vol){
      A = ((high + low)\2 - (move(high,1)+move(low,1))\2)*(high-low)\vol
      return ewmMean(A, alpha=2\15)
  }

翻译要点:
- move(x,1)=delay(x,1)=昨日值。
- (H+L)/2 = 当日中枢；昨日中枢 = (H1+L1)/2。
- A = (今日中枢 - 昨日中枢) * (H-L) / VOLUME
    = "中枢位移 × 当日振幅 / 量"（量归一化的中枢动量）。
- SMA(A,15,2)=ewmMean(alpha=2/15)（研报 SMA(n,m) alpha=m/n=2/15）。
- 分母 VOLUME 为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 15日指数平滑的"中枢位移×振幅/量"。
  高值=中枢上行且放量扩张（多方推进）；低值=中枢下行放量。量价动量维度。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha68Factor(FactorBase):
    name = "gtja_alpha68"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 16:  # move(1) + ewm(需至少1个有效值)
            return None
        high, low, vol = df["high"], df["low"], df["volume"]
        mid = (high + low) / 2
        mid1 = (high.shift(1) + low.shift(1)) / 2
        A = (mid - mid1) * (high - low) / vol.replace(0, np.nan)
        sma = sma_recursive(A, 15, 2)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
