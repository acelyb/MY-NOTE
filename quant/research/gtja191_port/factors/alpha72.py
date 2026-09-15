"""
GTJA191 Alpha72 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100, 15, 1)
DolphinDB:
  def gtjaAlpha72(close, high, low){
      A = (mmax(high,6)-close)\(mmax(high,6)-mmin(low,6))*100
      return ewmMean(A, alpha=1\15)
  }

翻译要点:
- A = (6日最高 - CLOSE) / (6日最高 - 6日最低) * 100 = 收盘相对6日高点的距离（0-100）。
  与 alpha57 的 RSV=(C-Lo)/(Hi-Lo) 互补：alpha72 = 100 - RSV（高点距离版）。
- SMA(A,15,1)=ewmMean(alpha=1/15)（研报 SMA(n,m) alpha=m/n=1/15）。
- 分母为0（6日无波动）时替换 nan。
- 与 alpha82 同源（窗口20），alpha72 用15日平滑。
- 无横截面算子，单标的可忠实还原。

语义: 15日指数平滑的"收盘距6日高点百分比"。
  高值=收盘远离6日高点（超卖/弱势），低值=接近6日高点（超买/强势）。
  是 alpha57 RSV 的反向版。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha72Factor(FactorBase):
    name = "gtja_alpha72"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # mmax/mmin(6) + ewm(需至少1个有效值)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        hi6 = high.rolling(6).max()
        lo6 = low.rolling(6).min()
        denom = (hi6 - lo6).replace(0, np.nan)
        A = (hi6 - close) / denom * 100
        sma = sma_recursive(A, 15, 1)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
