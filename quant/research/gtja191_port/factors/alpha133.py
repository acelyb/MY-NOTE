"""
GTJA191 Alpha133 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((20-HIGHDAY(HIGH,20))/20)*100 - ((20-LOWDAY(LOW,20))/20)*100
DolphinDB:
  def gtjaAlpha133(high, low){
      return (20 - (19 - mimax(high, 20))) \ 20 * 100 - (20 - (19 - mimin(low, 20))) \ 20 * 100
  }

翻译要点:
- HIGHDAY(HIGH,20) 返回"距今天数"(0=今天创20日高)。
  DolphinDB mimax 返回从窗口起点算的位置(0=最早)，故 HIGHDAY = 19 - mimax。
  DolphinDB 写 20 - (19-mimax) = 20 - HIGHDAY。
- base.ts_argmax 返回"距今天数"(0=今天)，与 HIGHDAY 口径一致，
  故 20 - HIGHDAY = 20 - ts_argmax(high,20)；LOWDAY 同理用 ts_argmin。
- (20-HIGHDAY)/20*100 = 高点位置越近(距今天数小)→20-小=大→因子大。
- 两项相减：高点越近且低点越远(低点距今天数大→20-小)→因子大。

语义: 20日内最高价位置与最低价位置的标准化差。
      最高价越近(近期创高)、最低价越远(未近期创低)→因子大→预期未来收益高（动量）。
      方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_argmax, ts_argmin


class Alpha133Factor(FactorBase):
    name = "gtja_alpha133"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # ts_argmax/ts_argmin(20)
            return None
        high, low = df["high"], df["low"]
        highday = ts_argmax(high, 20)   # 距今天数，0=今天
        lowday = ts_argmin(low, 20)
        val = ((20 - highday) / 20 * 100 - (20 - lowday) / 20 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
