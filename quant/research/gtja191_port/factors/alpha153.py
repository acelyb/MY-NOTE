"""
GTJA191 Alpha153 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (MEAN(CLOSE,3)+MEAN(CLOSE,6)+MEAN(CLOSE,12)+MEAN(CLOSE,24))/4
DolphinDB:
  def gtjaAlpha153(close){
      return (mavg(close, 3) + mavg(close, 6) + mavg(close, 12) + mavg(close, 24)) \ 4
  }

翻译要点:
- 四条收盘均线(3/6/12/24日)的简单平均。
- 最长链 mavg(24)。

语义: 多周期收盘均线的平均(平滑价格)。价高→因子大，方向以 IC 实测定（通常为价格水平/动量）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha153Factor(FactorBase):
    name = "gtja_alpha153"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # mavg(24)
            return None
        close = df["close"]
        m3 = close.rolling(3).mean()
        m6 = close.rolling(6).mean()
        m12 = close.rolling(12).mean()
        m24 = close.rolling(24).mean()
        val = ((m3 + m6 + m12 + m24) / 4).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
