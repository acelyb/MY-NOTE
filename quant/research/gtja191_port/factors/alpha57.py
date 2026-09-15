"""
GTJA191 Alpha57 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100, 3, 1)
DolphinDB:
  def gtjaAlpha57(close, high, low){
      A = (close - mmin(low,9))\(mmax(high,9) - mmin(low,9))*100
      return ewmMean(A, alpha=1\3)
  }

翻译要点:
- A = (CLOSE - 9日最低) / (9日最高 - 9日最低) * 100 = 9日窗口内收盘相对位置(0-100)，类 RSV/STOJ。
- SMA(A,3,1)=研报递归指数加权，Y_t = (A_{t-1}*1 + Y_{t-1}*(3-1))/3 = ewmMean(alpha=1/3)。
  ⚠️ DolphinDB 用 ewmMean(alpha=1/3) 直接对应 sma_recursive(A,3,1)。
- 分母为0（9日最高=最低，无波动）时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 9日 RSV(随机指标原始值) 的3日指数平滑。
  高值=收盘接近9日高点（超买），低值=接近9日低点（超卖）。
  反转类因子常见用法是低值看涨，但研报符号 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha57Factor(FactorBase):
    name = "gtja_alpha57"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:  # mmin/mmax(9)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        lo9 = low.rolling(9).min()
        hi9 = high.rolling(9).max()
        A = (close - lo9) / (hi9 - lo9).replace(0, np.nan) * 100
        sma = sma_recursive(A, 3, 1)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
