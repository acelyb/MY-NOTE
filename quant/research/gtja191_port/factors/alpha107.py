"""
GTJA191 Alpha107 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  -1 * RANK(OPEN-DELAY(HIGH,1)) * RANK(OPEN-DELAY(CLOSE,1)) * RANK(OPEN-DELAY(LOW,1))
DolphinDB:
  def gtjaAlpha107(open, close, high, low){
      return -1 * rowRank(open - mfirst(high, 2), percent=true)
              * rowRank(open - mfirst(close, 2), percent=true)
              * rowRank(open - mfirst(low, 2), percent=true)
  }

翻译要点:
- mfirst(high,2)=昨高 H_{t-1}，mfirst(close,2)=昨收 C_{t-1}，mfirst(low,2)=昨低 L_{t-1}。
- 三个缺口：开盘相对昨高/昨收/昨低的跳空 = OPEN-H1, OPEN-C1, OPEN-L1。
  三者同号：高开三者皆正，低开三者皆负。
- 三个 rowRank 横截面排名相乘，再取负。
- 单标的口径：rowRank 横截面 → 用 rolling(5) 时序 pct rank 近似（与 alpha10 同思路，有损）。
- 三者相乘放大同向信号、压制异向噪声（高开但跌破昨低等矛盾情形乘积小）。

语义: 开盘相对昨日(H/L/C)三缺口排名的乘积，取负——"开盘缺口强度"。
  与 alpha69(开盘跳空方向+冲高下探) 与 overnight_reversal(隔夜段) 不同：
  alpha107 纯看"开盘相对昨日整根K线的跳空"的截面排名乘积，强调跳空方向一致性。
  含三层横截面 rowRank 近似（三重有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha107Factor(FactorBase):
    name = "gtja_alpha107"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # mfirst(2) + rank(5)
            return None
        op, close, high, low = df["open"], df["close"], df["high"], df["low"]
        g1 = op - high.shift(1)    # OPEN - 昨高
        g2 = op - close.shift(1)   # OPEN - 昨收
        g3 = op - low.shift(1)     # OPEN - 昨低
        r1 = g1.rolling(5).rank(pct=True)
        r2 = g2.rolling(5).rank(pct=True)
        r3 = g3.rolling(5).rank(pct=True)
        val = (-r1 * r2 * r3).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
