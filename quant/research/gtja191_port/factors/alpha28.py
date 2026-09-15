"""
GTJA191 Alpha28 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  3*SMA(A,3,1) - 2*SMA(SMA(A,3,1),3,1)
  其中 A = (CLOSE-MIN(LOW,9))/(MAX(HIGH,9)-MIN(LOW,9)) （威廉/随机%K式位置）
DolphinDB:
  def gtjaAlpha28(close, high, low){
      A = (close - mmin(low,9))\(mmax(high,9)-mmin(low,9)*100)
      B = ewmMean(A,alpha=1\3)
      return 3*B - 2*ewmMean(B,alpha=1\3)
  }

翻译要点:
- A = (CLOSE - MIN(LOW,9)) / (MAX(HIGH,9) - MIN(LOW,9))：9日内收盘相对区间的位置∈[0,1]。
  ⚠️ DolphinDB 写法 `(mmax(high,9)-mmin(low,9)*100)` 有运算优先级歧义/笔误：
     按研报语义分母应为 (MAX(HIGH,9)-MIN(LOW,9))，这里 *100 疑为错放。
     研报原文是标准随机指标%K位置。以研报语义为准，分母=区间高度，不加×100。
- B = ewmMean(A, alpha=1/3) = SMA(A,3,1)（alpha=m/n=1/3）。
- 输出 = 3*B - 2*ewmMean(B, alpha=1/3) = 二次 EWM 平滑的"前瞻式"位置。
  这是 KDJ 中 J=3K-2D 的同构（KDJ: J=3K-2D），故 alpha28 本质是 KDJ-J 的单标的过程量。
- 分母=0（9日一字板）时替换 nan。无横截面算子，单标的可忠实还原。

语义: 收盘在9日区间的位置，经二次指数平滑后的 J 值（KDJ-J 同构）。
  超买(接近1)→可能反转下跌，超卖(接近0)→可能反转上涨。与 momentum/reversal 不同：
  这是"价格在近期区间的相对位置"而非"涨跌幅"，是震荡指标维度。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha28Factor(FactorBase):
    name = "gtja_alpha28"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 12:  # min/max(9) + 两次 ewm 需要一定暖机
            return None
        close, high, low = df["close"], df["high"], df["low"]
        lo9 = low.rolling(9).min()
        hi9 = high.rolling(9).max()
        rng = (hi9 - lo9).replace(0, np.nan)
        A = (close - lo9) / rng
        B = A.ewm(alpha=1 / 3, adjust=False).mean()
        val = (3 * B - 2 * B.ewm(alpha=1 / 3, adjust=False).mean()).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
