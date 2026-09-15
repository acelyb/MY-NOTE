"""
GTJA191 Alpha50 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM(下移日波幅,12)/(下移+上移) - SUM(上移日波幅,12)/(下移+上移)
  （即 alpha49 的"下移占比" - "上移占比" = 2*下移占比 - 1）
DolphinDB:
  def gtjaAlpha50(high, low){
      sum1 = msum(iif((high + low) <= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      sum2 = msum(iif((high + low) >= (mfirst(high, 2) + mfirst(low, 2)), 0,
                     max(abs(high - mfirst(high, 2)), abs(low - mfirst(low, 2)))), 12)
      return sum1 \ (sum1 + sum2) - sum2 \ (sum1 + sum2)
  }

翻译要点:
- 与 alpha49 同源，波幅定义、窗口一致。
- ⚠️ DolphinDB 这里 sum1/sum2 的条件与 alpha49 互换：
    alpha50 的 sum1: (H+L)<=昨 取0 → 即"上移日波幅累积"（alpha49 的 sum2）。
    alpha50 的 sum2: (H+L)>=昨 取0 → 即"下移日波幅累积"（alpha49 的 sum1）。
  按代码字面：返回 sum1/(sum1+sum2) - sum2/(sum1+sum2) = (上移占比 - 下移占比)。
  即 alpha50 = -（alpha49 居中化），是 alpha49 的对称/去均值版（差值∈[-1,1]，0为中性）。
- 分母为0时替换 nan。无横截面算子，单标的可忠实还原。

语义: DMI 式方向波幅的"上移占比-下移占比"，去均值对称版。
  +1=完全上移波幅，-1=完全下移波幅，0=多空均衡。与 alpha49 高度同源（线性变换），
  保留一个即可，此处实为做交叉验证。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha50Factor(FactorBase):
    name = "gtja_alpha50"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:
            return None
        high, low = df["high"], df["low"]
        h1, l1 = high.shift(1), low.shift(1)
        hl = high + low
        hl1 = h1 + l1
        tr = np.maximum((high - h1).abs(), (low - l1).abs())
        # sum1: (H+L)<=昨 取0 → 其余（上移日）波幅
        s1 = pd.Series(np.where((hl <= hl1).values, 0.0, tr), index=high.index)
        # sum2: (H+L)>=昨 取0 → 其余（下移日）波幅
        s2 = pd.Series(np.where((hl >= hl1).values, 0.0, tr), index=high.index)
        sum1 = s1.rolling(12).sum()
        sum2 = s2.rolling(12).sum()
        denom = (sum1 + sum2).replace(0, np.nan)
        val = (sum1 / denom - sum2 / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
