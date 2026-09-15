"""
GTJA191 Alpha187 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((OPEN<=DELAY(OPEN,1)?0:MAX((HIGH-OPEN),(OPEN-DELAY(OPEN,1)))),20)
DolphinDB:
  def gtjaAlpha187(open, high){
      return msum(iif(open <= mfirst(open, 2), 0, max(high - open, open - mfirst(open, 2))), 20)
  }

翻译要点:
- mfirst(open,2)=delay(open,1)=前日开盘。
- 条件 open<=delay(open,1)（今日开盘不高于前日开盘，未跳空高开）：
  - 成立: 记 0。
  - 不成立（跳空高开）: MAX(high-open, open-前日open) = 高开后的上影或跳空幅度中的大者。
- msum(...,20)=20日累计（跳空高开日的"上影或跳空"最大值之和）。
- 最长链：delay(1)+msum(20) = 21 行起算。

语义: 20日跳空高开日的"上影或跳空幅度"累计。
      累计越大→上攻尝试越多→因子大→预期未来收益高（动量/突破），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha187Factor(FactorBase):
    name = "gtja_alpha187"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(1) + msum(20)
            return None
        op, high = df["open"], df["high"]
        do1 = op.shift(1)                          # DELAY(OPEN,1)
        term = np.maximum(high - op, op - do1)     # MAX(HIGH-OPEN, OPEN-DELAY(OPEN,1))
        A = pd.Series(np.where(op <= do1, 0.0, term), index=df.index)
        val = ts_sum(A, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
