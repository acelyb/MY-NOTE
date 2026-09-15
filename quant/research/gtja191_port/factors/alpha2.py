"""
GTJA191 Alpha2 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * (DELTA((((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW)), 1))
DolphinDB:
  def gtjaAlpha2(close, high, low){
      tmp = (close - low - (high - close)) \\ (high - low)
      return -1 * (tmp - mfirst(tmp, 2))
  }

翻译要点:
- tmp = ((CLOSE-LOW)-(HIGH-CLOSE))/(HIGH-LOW) —— 收盘在日内高低区间的位置
  (CLOSE-LOW)=收盘离低的距离；(HIGH-CLOSE)=收盘离高的距离；
  两者差 = 2*CLOSE-HIGH-LOW，归一化到(HIGH-LOW)后∈[-1,1]：
  收盘在中点→0；收盘接近最高→+1；接近最低→-1。
- DELTA(tmp,1)=tmp - mfirst(tmp,2)（mfirst(x,2)=前2期的值，即 x_{t-2}；这里取差即 tmp_t - tmp_{t-1}，等价 delay1 差分）
  注意 DolphinDB mfirst(tmp,2) 是 tmp 整体前移1期（mfirst(x,n)取窗口n的首值=最旧值，
  对齐到当前即 x_{t-n+1}），n=2 即 x_{t-1}。故 tmp - mfirst(tmp,2) = tmp_t - tmp_{t-1} = delta(tmp,1)。
- 整体取负。

语义: 收盘日内位置的一阶差分取负——日内位置上升(收盘走高)→因子下降，
  即"收盘走强后预期反转"。属短周期反转类。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha2Factor(FactorBase):
    name = "gtja_alpha2"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 3:
            return None
        close, high, low = df["close"], df["high"], df["low"]
        denom = (high - low).replace(0, pd.NA)
        tmp = ((close - low) - (high - close)) / denom
        delta = tmp - tmp.shift(1)  # DELTA(tmp,1)
        val = delta.iloc[-1]
        if pd.isna(val):
            return None
        return -float(val)
