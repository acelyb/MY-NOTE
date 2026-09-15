"""
GTJA191 Alpha189 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(ABS(CLOSE-MEAN(CLOSE,6)),6)
DolphinDB:
  def gtjaAlpha189(close){
      return mavg(abs(close - mavg(close, 6)), 6)
  }

翻译要点:
- mavg(close,6)=6日收盘均值；close-mavg=偏离；abs 取绝对值。
- mavg(abs(偏离),6)=6日平均绝对偏离 = 6日 MAD 均值版（波动率维度）。
- 最长链：mavg(6)+mavg(6) = 12 行起算。

语义: 6日收盘的平均绝对偏离（类 MAD 波动率）。
      偏离越大→波动越大→因子大，波动率维度，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha189Factor(FactorBase):
    name = "gtja_alpha189"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 12:  # mavg(6) + mavg(6)
            return None
        close = df["close"]
        dev = (close - close.rolling(6).mean()).abs()
        val = dev.rolling(6).mean().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
