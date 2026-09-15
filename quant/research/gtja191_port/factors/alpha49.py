"""
GTJA191 Alpha49 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM(((H+L)>=(DELAY(H,1)+DELAY(L,1)) ? 0 : MAX(|H-DELAY(H,1)|,|L-DELAY(L,1)|)), 12)
  / ( 上式 + SUM(((H+L)<=(DELAY(H,1)+DELAY(L,1)) ? 0 : MAX(|H-DELAY(H,1)|,|L-DELAY(L,1)|)), 12) )
DolphinDB:
  def gtjaAlpha49(high, low){
      sum1 = msum(iif((high + low) >= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      sum2 = msum(iif((high + low) <= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      return sum1 \ (sum1 + sum2)
  }

翻译要点:
- mfirst(high,2)=昨高 H_{t-1}，mfirst(low,2)=昨低 L_{t-1}。
- MAX(|H-H1|,|L-L1|)=当日相对昨日的"真实波幅"极差（DMI 的 TR 变体，用 H/L 而非含昨收）。
- sum1: 当 (H+L) >= 昨(H+L)（即今日中枢上移）时记0，否则记极差 → "中枢下移日的波幅累积"。
  ⚠️ 注意研报/DolphinDB 的条件方向：>= 时取0，说明 sum1 累积的是"中枢未上移（下移或持平）"的波幅。
- sum2: 当 (H+L) <= 昨(H+L)（中枢下移或持平）时记0，否则记极差 → "中枢上移日的波幅累积"。
- 返回 sum1/(sum1+sum2) ∈[0,1]：中枢下移波幅占总波幅的比例。
- 分母为0（12日无波幅）时替换 nan。无横截面算子，单标的可忠实还原。

语义: DMI 式方向波幅占比——下移波幅占总波幅的比例，高值=下跌主导。
  与 alpha50(差值版) 互补：alpha49 是下移占比，alpha50 是下移占比-上移占比。
  是"方向性波动"维度，区别于 low_vol(总波动)。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha49Factor(FactorBase):
    name = "gtja_alpha49"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # mfirst(2) + msum(12)
            return None
        high, low = df["high"], df["low"]
        h1, l1 = high.shift(1), low.shift(1)
        hl = high + low
        hl1 = h1 + l1
        tr = np.maximum((high - h1).abs(), (low - l1).abs())  # 极差波幅
        # sum1: (H+L)>=昨 取0，否则取波幅
        s1 = pd.Series(np.where((hl >= hl1).values, 0.0, tr), index=high.index)
        # sum2: (H+L)<=昨 取0，否则取波幅
        s2 = pd.Series(np.where((hl <= hl1).values, 0.0, tr), index=high.index)
        sum1 = s1.rolling(12).sum()
        sum2 = s2.rolling(12).sum()
        denom = (sum1 + sum2).replace(0, np.nan)
        val = (sum1 / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
