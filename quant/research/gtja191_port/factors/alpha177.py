"""
GTJA191 Alpha177 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((20-HIGHDAY(HIGH,20))/20)*100
DolphinDB:
  def gtjaAlpha177(high){
      return (20 - (19 - mimax(high, 20))) \ 20 * 100
  }

翻译要点:
- HIGHDAY(HIGH,20) 返回"距今天数"(0=今天创20日高)。
  DolphinDB mimax 返回从窗口起点算的位置(0=最早)，故 HIGHDAY = 19 - mimax。
  DolphinDB 写 20 - (19-mimax) = 20 - HIGHDAY。
- base.ts_argmax 返回"距今天数"(0=今天)，与 HIGHDAY 口径一致，
  故 20 - HIGHDAY = 20 - ts_argmax(high,20)。
- (20-HIGHDAY)/20*100 = 高点越近(距今天数小)→20-小=大→因子大。
- 与 alpha103(LOW 时效)、alpha133(高低时效差) 同系列。
- 最长链 ts_argmax(20)=20 行起算。

语义: 20日最高价的"时效"。最高价越近(近期创高)→因子大→预期未来收益高（动量），
      今天创20日新高→HIGHDAY=0→值=100。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_argmax


class Alpha177Factor(FactorBase):
    name = "gtja_alpha177"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # ts_argmax(20)
            return None
        high = df["high"]
        highday = ts_argmax(high, 20)   # 距今天数，0=今天
        val = ((20 - highday) / 20 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
