"""
GTJA191 Alpha98 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  ((((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))<0.05) ||
    ((DELTA((SUM(CLOSE,100)/100),100)/DELAY(CLOSE,100))==0.05))
   ? (-1*(CLOSE-TSMIN(CLOSE,100)))
   : (-1*DELTA(CLOSE,3)))
DolphinDB:
  def gtjaAlpha98(close){
      cond1 = ((msum(close, 100) \ 100 - mfirst(msum(close, 100) \ 100, 101)) \ mfirst(close, 101) < 0.05)
      cond2 = ((msum(close, 100) \ 100 - mfirst(msum(close, 100) \ 100, 101)) \ mfirst(close, 101) == 0.05)
      return iif(cond1 || cond2, -1 * (close - mmin(close, 100)), -1 * (close - mfirst(close, 4)))
  }

翻译要点:
- MA100 变化率 r = (MA100_t - MA100_{t-100}) / close_{t-100}。
  msum(close,100)/100 = MA100；mfirst(MA100,101)=MA100_{t-100}；mfirst(close,101)=close_{t-100}。
- 条件 r<=0.05（源码 cond1 为 <0.05, cond2 为 ==0.05, 逻辑或即 <=0.05）：
  真 → -(close - ts_min(close,100)) = 负的"收盘相对100日最低的涨幅"。
  假 → -(close - close_{t-3}) = 负的3日涨幅。
- iif 用 np.where。==0.05 浮点严格比较照源码翻译（实际罕见命中）。
- mfirst(close,101)=delay(close,100)；mfirst(close,4)=delay(close,3)。

语义: 长期均线变化率分段。长期均线变化温和(<=5%)→取负的100日低位反弹幅度；
  长期趋势强劲(>5%)→取负的3日涨幅（反向）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_min, ts_sum


class Alpha98Factor(FactorBase):
    name = "gtja_alpha98"

    def calc(self, df: pd.DataFrame) -> float | None:
        # 最长链: msum(100) + mfirst(101) → 需 200 行；mmin(100) 需 100 行
        if len(df) < 200:
            return None
        close = df["close"]
        ma100 = ts_sum(close, 100) / 100            # MA100
        ma100_prev = ma100.shift(100)               # mfirst(MA100,101)
        c100_prev = close.shift(100)                # mfirst(close,101)=DELAY(CLOSE,100)
        r = (ma100 - ma100_prev) / c100_prev.replace(0, np.nan)
        cond = (r <= 0.05)  # cond1||cond2 即 <=0.05
        ts_min100 = ts_min(close, 100)
        delta3 = close - close.shift(3)             # DELTA(CLOSE,3)
        val = np.where(cond, -1.0 * (close - ts_min100), -1.0 * delta3)
        val = pd.Series(val, index=close.index).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
