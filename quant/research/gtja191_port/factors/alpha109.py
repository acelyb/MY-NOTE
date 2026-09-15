"""
GTJA191 Alpha109 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)
DolphinDB:
  def gtjaAlpha109(high, low){
      A =  ewmMean(high-low,alpha=2\10)
      return A \ ewmMean(A,alpha=2\10)
  }

翻译要点:
- A = SMA(HIGH-LOW,10,2)=ewmMean(alpha=2/10) 对日内振幅做指数平滑。
- 分母 = SMA(A,10,2)=ewmMean(A, alpha=2/10)（A 的再平滑）。
- 比值 = 当日平滑振幅 / 二次平滑振幅，类似振幅的动量比。
- 分母为0时除零置 NaN。

语义: 日内振幅的平滑值/再平滑值。振幅放大→A>分母→因子大→
  方向以 IC 实测定（可能波动放大反转）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ema_mean


class Alpha109Factor(FactorBase):
    name = "gtja_alpha109"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:  # ewm 递归
            return None
        high, low = df["high"], df["low"]
        A = ema_mean(high - low, 2 / 10)       # SMA(HIGH-LOW,10,2)
        denom = ema_mean(A, 2 / 10)            # SMA(A,10,2)
        val = (A / denom.replace(0, np.nan)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
