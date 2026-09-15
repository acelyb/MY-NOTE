"""
GTJA191 Alpha145 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (MEAN(VOLUME,9)-MEAN(VOLUME,26))/MEAN(VOLUME,12)*100
DolphinDB:
  def gtjaAlpha145(vol){
      return (mavg(vol, 9) - mavg(vol, 26)) \ mavg(vol, 12) * 100
  }

翻译要点:
- mavg(vol,n)=vol.rolling(n).mean()。
- 9日均量-26日均量(快慢线差) 除以12日均量 归一化 再×100。
- 除零：12日均量为 0 时置 NaN。
- 最长链 mavg(26)。

语义: 成交量快慢均线差归一化(类 MACD 量能柱)。放量→快线>慢线→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha145Factor(FactorBase):
    name = "gtja_alpha145"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 26:  # mavg(26)
            return None
        vol = df["volume"]
        m9 = vol.rolling(9).mean()
        m26 = vol.rolling(26).mean()
        m12 = vol.rolling(12).mean()
        val = ((m9 - m26) / m12.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
