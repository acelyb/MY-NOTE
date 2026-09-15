"""
GTJA191 Alpha93 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((OPEN>=DELAY(OPEN,1)?0:MAX((OPEN-LOW),(OPEN-DELAY(OPEN,1)))),20)
DolphinDB:
  def gtjaAlpha93(open, low){
      return msum(iif(open >= mfirst(open, 2), 0, max(open - low, open - mfirst(open, 2))), 20)
  }

翻译要点:
- mfirst(open,2)=delay(open,1)；iif(open>=open_{t-1}, 0, max(open-low, open-open_{t-1}))。
- 开低走(开<昨开)时取 max(开盘-最低, 开盘-昨开) 的下跌幅度，否则0；过去20日求和。
- msum=ts_sum；iif=np.where；max 用 np.maximum 逐元素取大。

语义: 20日开盘下跌幅度累计。开盘持续低开且幅度大→因子大→
  方向以 IC 实测定（可能为反转信号）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha93Factor(FactorBase):
    name = "gtja_alpha93"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(1) + sum(20)
            return None
        op, low = df["open"], df["low"]
        op_prev = op.shift(1)   # DELAY(OPEN,1)
        inner = np.where(op >= op_prev, 0.0,
                         np.maximum(op - low, op - op_prev))
        inner = pd.Series(inner, index=op.index)
        val = ts_sum(inner, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
