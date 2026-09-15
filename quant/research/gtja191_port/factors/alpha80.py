"""
GTJA191 Alpha80 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (VOLUME-DELAY(VOLUME,5))/DELAY(VOLUME,5)*100
DolphinDB:
  def gtjaAlpha80(vol){
      return (vol - move(vol, 5)) \ move(vol, 5) * 100
  }

翻译要点:
- move(vol,5)=delay(vol,5)=5日前成交量。
- 返回 (当量 - 5日前量)/5日前量 * 100 = 成交量5日变化率(%)。
- 分母为0（5日前无成交）时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 成交量5日变化率(%)。正值=放量，负值=缩量。
  量能动量维度，反映短期成交量趋势。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha80Factor(FactorBase):
    name = "gtja_alpha80"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # move(5)
            return None
        vol = df["volume"]
        v5 = vol.shift(5)
        val = ((vol - v5) / v5.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
