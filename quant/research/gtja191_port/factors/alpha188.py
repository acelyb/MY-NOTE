"""
GTJA191 Alpha188 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((HIGH-LOW - SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2))*100
DolphinDB:
  def gtjaAlpha188(high, low){
      A = ewmMean(high-low,alpha=2\11)
      return (high - low - A) \ A * 100
  }

翻译要点:
- high-low=日内振幅；A = SMA(high-low,11,2) = ewmMean(alpha=2/11) 递归指数加权均值。
- (振幅 - A)/A*100 = 振幅相对其SMA的偏离(%)。
- 除零：A=0 时置 NaN。
- ewm 理论全历史有效，需足够行数收敛；取 11 行起算。

语义: 日内振幅相对其11日SMA的偏离百分比。
      振幅扩张→因子大→波动放大（可能突破/变盘），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha188Factor(FactorBase):
    name = "gtja_alpha188"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 11:  # ewm(2/11) 需足够历史
            return None
        high, low = df["high"], df["low"]
        hl = high - low
        A = sma_recursive(hl, 11, 2)              # SMA(HIGH-LOW,11,2)
        val = ((hl - A) / A.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
