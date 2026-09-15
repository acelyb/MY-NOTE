"""
GTJA191 Alpha52 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM(MAX(0, HIGH-DELAY((H+L+C)/3,1)), 26)
  / SUM(MAX(0, DELAY((H+L+C)/3,1)-LOW), 26) * 100
DolphinDB:
  def gtjaAlpha52(close, high, low){
      return msum(max(0, high - mfirst((high + low + close) \ 3, 2)), 26)
              \ msum(max(0, mfirst((high + low + close) \ 3, 2) - low), 26) * 100
  }

翻译要点:
- 典型价 TP=(H+L+C)/3；mfirst(TP,2)=昨日典型价 TP_{t-1}。
- 分子: SUM(MAX(0, HIGH - TP_{t-1}), 26) = 26日内"高点突破昨日中枢"的正向幅度累积（多头力）。
- 分母: SUM(MAX(0, TP_{t-1} - LOW), 26) = 26日内"低点跌破昨日中枢"的负向幅度累积（空头力）。
- 比值×100 ∈[0,∞)：多头力/空头力。>100 多头占优，<100 空头占优。
- 分母=0时替换 nan。无横截面算子，单标的可忠实还原。

语义: 以昨日典型价为基准的多空力量比（26日）。
  与 alpha49/50(用昨H/L中枢) 不同：这里用昨日典型价(TP)作基准，且分子分母分别取正向/负向幅度
  （类似 RSI 但用 TP 突破而非涨跌幅）。是"以中枢为锚的多空力道"维度。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha52Factor(FactorBase):
    name = "gtja_alpha52"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 27:  # mfirst(2) + msum(26)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        tp = (high + low + close) / 3
        tp1 = tp.shift(1)
        up = (high - tp1).clip(lower=0)      # 多头力
        dn = (tp1 - low).clip(lower=0)       # 空头力
        sup = up.rolling(26).sum()
        sdn = dn.rolling(26).sum().replace(0, np.nan)
        val = (sup / sdn * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
