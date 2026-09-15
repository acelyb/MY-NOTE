"""
GTJA191 Alpha159 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  ((CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),6))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),6)*12*24
  +(CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),12))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),12)*6*24
  +(CLOSE-SUM(MIN(LOW,DELAY(CLOSE,1)),24))/SUM(MAX(HIGH,DELAY(CLOSE,1))-MIN(LOW,DELAY(CLOSE,1)),24)*6*24)
  *100/(6*12+6*24+12*24)
DolphinDB:
  def gtjaAlpha159(close, high, low){
      tmp1 = (close - msum(min(low, mfirst(close, 2)), 6)) \ msum(max(high, mfirst(close, 2)) - min(low, mfirst(close, 2)), 6) * 12 * 24
      tmp2 = (close - msum(min(low, mfirst(close, 2)), 12)) \ msum(max(high, mfirst(close, 2)) - min(low, mfirst(close, 2)), 12) * 6 * 24
      tmp3 = (close - msum(min(low, mfirst(close, 2)), 24)) \ msum(max(high, mfirst(close, 2)) - min(low, mfirst(close, 2)), 24) * 6 * 24
      return (tmp1 + tmp2 + tmp3) * 100 \ (6 * 12 + 6 * 24 + 12 * 24)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘。
- min(low, dc1) / max(high, dc1) 构造以"前收-今日高低"为界的扩展区间。
- 三档窗口(6/12/24) 各算: (收盘-区间下界和)/(区间宽度和)*权重(12*24/6*24/6*24)。
- 三项求和 ×100 /(6*12+6*24+12*24=504) 归一化。
- 除零：区间宽度求和为 0 时该项置 NaN。
- 最长链 delay(1)+msum(24)=25 行起算。

语义: 多窗口(6/12/24)收盘在"高低扩展区间"位置的加权平均(类 Stochastic 多周期)。
      收盘接近区间上沿→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha159Factor(FactorBase):
    name = "gtja_alpha159"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:  # delay(1) + msum(24)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        dc1 = close.shift(1)                       # DELAY(CLOSE,1)
        lo = np.minimum(low, dc1)                  # MIN(LOW,DC1)
        hi = np.maximum(high, dc1)                 # MAX(HIGH,DC1)
        width = hi - lo
        lo_s = pd.Series(lo, index=df.index)
        width_s = pd.Series(width, index=df.index)

        def _term(n, w):
            num = close - ts_sum(lo_s, n)
            den = ts_sum(width_s, n).replace(0, np.nan)
            return num / den * w

        tmp1 = _term(6, 12 * 24)
        tmp2 = _term(12, 6 * 24)
        tmp3 = _term(24, 6 * 24)
        val = ((tmp1 + tmp2 + tmp3) * 100 / (6 * 12 + 6 * 24 + 12 * 24)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
