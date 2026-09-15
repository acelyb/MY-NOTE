"""
GTJA191 Alpha55 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM( 16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))
       / ( 嵌套 iif 三分支分母 )
       * MAX(ABS(HIGH-DELAY(CLOSE,1)), ABS(LOW-DELAY(CLOSE,1)))
     , 20)
DolphinDB:
  def gtjaAlpha55(open, close, high, low){
      tmp1 = 16 * (close - mfirst(close, 2) + (close - open) \ 2 + mfirst(close, 2) - mfirst(open, 2))
      cond = abs(high - mfirst(close, 2)) > abs(low - mfirst(close, 2)) && abs(high - mfirst(close, 2)) > abs(high - mfirst(low, 2))
      iftrue = abs(high - mfirst(close, 2)) + abs(low - mfirst(close, 2)) \ 2 + abs(mfirst(close, 2) - mfirst(open, 2)) \ 4
      cond2 = abs(low - mfirst(close, 2)) > abs(high - mfirst(low, 2)) && abs(low - mfirst(close, 2)) > abs(high - mfirst(close, 2))
      iftrue2 = abs(low - mfirst(close, 2)) + abs(high - mfirst(low, 2)) \ 2 + abs(mfirst(close, 2) - mfirst(open, 2)) \ 4
      iffalse2 = abs(high - mfirst(low, 2)) + abs(mfirst(close, 2) - mfirst(open, 2)) \ 4
      iffalse = iif(cond2, iftrue2, iffalse2)
      tmp2 = iif(cond, iftrue, iffalse)
      tmp3 = max(abs(high - mfirst(close, 2)), abs(low - mfirst(close, 2)))
      return msum(tmp1 \ tmp2 * tmp3, 20)
  }

翻译要点:
- mfirst(x,2)=delay(x,1)=昨日值。
- 分子 tmp1 = 16*(C-C1 + (C-O)/2 + C1-O1)，其中 C1=昨收, O1=昨开。
- 分母 tmp2 为三分支 iif（ Chandler 因子形式的"波幅加权"）：
    cond: |H-C1| 最大（大于 |L-C1| 且大于 |H-L1|） → 用 |H-C1| + |L-C1|/2 + |C1-O1|/4
    否则 cond2: |L-C1| 最大（大于 |H-L1| 且大于 |H-C1|） → 用 |L-C1| + |H-L1|/2 + |C1-O1|/4
    否则（|H-L1| 最大） → 用 |H-L1| + |C1-O1|/4
- tmp3 = MAX(|H-C1|, |L-C1|)。
- 整体取20日求和。
- 分母可能为0（所有项为0），需替换 nan 避免除零。
- 无横截面算子，单标的可忠实还原。

语义: 类似 Chandler 动量因子的"波幅归一化日内动量累积"，20日加总。
  反映日内价格扩展相对昨日波幅的强度，方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha55Factor(FactorBase):
    name = "gtja_alpha55"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mfirst(2) + msum(20)
            return None
        op, close, high, low = df["open"], df["close"], df["high"], df["low"]
        c1 = close.shift(1)
        o1 = op.shift(1)
        l1 = low.shift(1)

        # 分子
        tmp1 = 16 * (close - c1 + (close - op) / 2 + c1 - o1)

        # 分母三分支
        a_hc = (high - c1).abs()
        a_lc = (low - c1).abs()
        a_hl = (high - l1).abs()
        a_co = (c1 - o1).abs()

        cond = (a_hc > a_lc) & (a_hc > a_hl)
        cond2 = (a_lc > a_hl) & (a_lc > a_hc)
        iftrue = a_hc + a_lc / 2 + a_co / 4
        iftrue2 = a_lc + a_hl / 2 + a_co / 4
        iffalse2 = a_hl + a_co / 4
        iffalse = pd.Series(np.where(cond2.values, iftrue2.values, iffalse2.values), index=high.index)
        tmp2 = pd.Series(np.where(cond.values, iftrue.values, iffalse.values), index=high.index)

        tmp3 = np.maximum(a_hc, a_lc)

        ratio = tmp1 / tmp2.replace(0, np.nan) * tmp3
        val = ratio.rolling(20).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
