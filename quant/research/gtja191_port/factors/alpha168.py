"""
GTJA191 Alpha168 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (-1*VOLUME/MEAN(VOLUME,20))
DolphinDB:
  def gtjaAlpha168(vol){
      return -1 * vol \ mavg(vol, 20)
  }

翻译要点:
- mavg(vol,20)=20日成交量均值；vol/mavg = 量比。
- 取负：量比越大→因子越小。
- 除零：20日均量为 0 时置 NaN。
- 最长链 mavg(20)。

语义: 负量比。放量→因子小→预期未来收益低（量价反转/放量见顶视角），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha168Factor(FactorBase):
    name = "gtja_alpha168"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # mavg(20)
            return None
        vol = df["volume"]
        m20 = vol.rolling(20).mean()
        val = (-vol / m20.replace(0, np.nan)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
