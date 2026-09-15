"""
GTJA191 Alpha38 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (((SUM(HIGH,20)/20) < HIGH) ? (-1 * DELTA(HIGH,2)) : 0)
DolphinDB:
  def gtjaAlpha38(high){
      return iif((msum(high, 20) \ 20) < high, -1 * (high - mfirst(high, 3)), 0)
  }

翻译要点:
- msum(high,20)/20 = ts_mean(high,20)（20日高价均值）。
- mfirst(high,3)=delay(high,2)=DELTA(high,2)（研报 DELTA(HIGH,2)）。
- 条件：当 high > 20日高价均值（创新高/突破），输出 -DELTA(HIGH,2)；否则0。
- iif 用 np.where 实现。
- 无横截面算子，单标的可忠实还原。

语义: 突破20日高价均值时，取 -2日高价动量；否则为0。
  即"创新高时看空2日动量"（反转逻辑：突破后短期回调）。属条件反转因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_mean, delay


class Alpha38Factor(FactorBase):
    name = "gtja_alpha38"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 22:  # mean(20)+delay(2)+1
            return None
        high = df["high"]
        mean20 = ts_mean(high, 20)
        cond = mean20 < high
        delta2 = high - delay(high, 2)
        val_series = pd.Series(np.where(cond, -delta2, 0.0), index=high.index)
        val = val_series.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
