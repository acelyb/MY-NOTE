"""
GTJA191 Alpha111 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(VOL*((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW),11,2)-SMA(VOL*((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW),4,2)
DolphinDB:
  def gtjaAlpha111(close, high, low, vol){
      A = vol*((close-low)-(high-close))\(high-low)
      return ewmMean(A,alpha=2\11) - ewmMean(A,alpha=2\4)
  }

翻译要点:
- A = vol * ((close-low)-(high-close)) / (high-low)
  = vol * (2*close - high - low)/(high-low) = 量加权的日内对称位置(-1~1)。
- SMA(A,11,2)=ewmMean(alpha=2/11)；SMA(A,4,2)=ewmMean(alpha=2/4)。
- 输出 = 长期平滑 - 短期平滑（类似慢快线差，方向需注意）。
- (high-low)=0 时除零置 NaN。

语义: 量加权日内位置的快慢均线差。短期平滑(4)高于长期(11)→因子为负→
  方向以 IC 实测定。注意与 MACD 快慢线惯例相反(此处是慢减快)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ema_mean


class Alpha111Factor(FactorBase):
    name = "gtja_alpha111"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:  # ewm 递归
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        rng = (high - low).replace(0, np.nan)
        A = vol * ((close - low) - (high - close)) / rng
        slow = ema_mean(A, 2 / 11)   # SMA(A,11,2)
        fast = ema_mean(A, 2 / 4)    # SMA(A,4,2)
        val = (slow - fast).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
