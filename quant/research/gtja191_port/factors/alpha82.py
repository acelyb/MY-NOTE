"""
GTJA191 Alpha82 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100, 20, 1)
DolphinDB:
  def gtjaAlpha82(close, high, low){
      A = (mmax(high,6)-close)\(mmax(high,6)-mmin(low,6))*100
      return ewmMean(A, alpha=1\20)
  }

翻译要点:
- 与 alpha72 同源，A 完全相同；差别在平滑窗口：alpha72 用 SMA(15,1)，alpha82 用 SMA(20,1)。
- A = (6日最高 - CLOSE) / (6日最高 - 6日最低) * 100 = 收盘相对6日高点的距离(0-100)。
- SMA(A,20,1)=ewmMean(alpha=1/20)（研报 SMA(n,m) alpha=m/n=1/20）。
- 分母为0（6日无波动）时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 20日指数平滑的"收盘距6日高点百分比"。
  比 alpha72(15日平滑) 更慢。高值=超卖/弱势，低值=超买/强势。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha82Factor(FactorBase):
    name = "gtja_alpha82"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # mmax/mmin(6) + ewm(需至少1个有效值)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        hi6 = high.rolling(6).max()
        lo6 = low.rolling(6).min()
        denom = (hi6 - lo6).replace(0, np.nan)
        A = (hi6 - close) / denom * 100
        sma = sma_recursive(A, 20, 1)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
