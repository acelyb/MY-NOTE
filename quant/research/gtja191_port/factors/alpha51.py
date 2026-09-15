"""
GTJA191 Alpha51 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM(((HIGH+LOW)<=(DELAY(HIGH,1)+DELAY(LOW,1)) ? 0 : MAX(|H-DELAY(H,1)|,|L-DELAY(L,1)|)), 12)
  / ( 上式 + SUM(((HIGH+LOW)>=(DELAY(HIGH,1)+DELAY(LOW,1)) ? 0 : MAX(|H-DELAY(H,1)|,|L-DELAY(L,1)|)), 12) )
DolphinDB:
  def gtjaAlpha51(high, low){
      sum1 = msum(iif((high + low) <= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      sum2 = msum(iif((high + low) >= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      return sum1 \ (sum1 + sum2)
  }

翻译要点:
- mfirst(x,2)=delay(x,1)=昨日值。
- 波幅 tr=MAX(|H-H1|,|L-L1|)（DMI 式真实波幅变体，用 H/L 而非含昨收）。
- sum1: (H+L)<=昨 取0，否则取波幅 → "中枢上移日的波幅累积"（下移或持平时记0的反面）。
  注意条件方向：<= 时取0，所以 sum1 累积的是"中枢未下移（上移或持平）"的波幅。
- sum2: (H+L)>=昨 取0，否则取波幅 → "中枢下移日的波幅累积"。
- 返回 sum1/(sum1+sum2) ∈[0,1]：上移波幅占总波幅的比例。
- 与 alpha49/50 同源（波幅定义、窗口一致），但条件配对相反：
    alpha49 返回"下移占比"（alpha49 sum1 取 >= 时为0）。
    alpha51 返回"上移占比"（alpha51 sum1 取 <= 时为0）。
  逻辑上 alpha51 ≈ 1 - alpha49（在非持平日上）。
- 分母为0时替换 nan。无横截面算子，单标的可忠实还原。

语义: DMI 式方向波幅占比——上移波幅占总波幅的比例，高值=上涨主导。
  与 alpha49（下移占比）互补对称。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha51Factor(FactorBase):
    name = "gtja_alpha51"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # mfirst(2) + msum(12)
            return None
        high, low = df["high"], df["low"]
        h1, l1 = high.shift(1), low.shift(1)
        hl = high + low
        hl1 = h1 + l1
        tr = np.maximum((high - h1).abs(), (low - l1).abs())
        # sum1: (H+L)<=昨 取0，否则取波幅 → 上移日波幅累积
        s1 = pd.Series(np.where((hl <= hl1).values, 0.0, tr), index=high.index)
        # sum2: (H+L)>=昨 取0，否则取波幅 → 下移日波幅累积
        s2 = pd.Series(np.where((hl >= hl1).values, 0.0, tr), index=high.index)
        sum1 = s1.rolling(12).sum()
        sum2 = s2.rolling(12).sum()
        denom = (sum1 + sum2).replace(0, np.nan)
        val = (sum1 / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
