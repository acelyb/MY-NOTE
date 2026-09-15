"""
GTJA191 Alpha43 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),6)
DolphinDB:
  def gtjaAlpha43(close, vol){
      return msum(iif(close > mfirst(close, 2), vol, iif(close < mfirst(close, 2), -vol, 0)), 6)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=DELAY(CLOSE,1)。
- 三分支：上涨日取+vol，下跌日取-vol，持平取0（带方向成交量，OBV 的6日和）。
- iif 用 np.where 嵌套实现。
- msum(...,6)=ts_sum(...,6)。
- 无横截面算子，单标的可忠实还原。

语义: 过去6日带方向成交量和（上涨+量，下跌-量）。正值→上涨放量主导；负值→下跌放量主导。
  属量能动量因子（OBV 变体），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay, ts_sum


class Alpha43Factor(FactorBase):
    name = "gtja_alpha43"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # delay(1)+sum(6)+1
            return None
        close, vol = df["close"], df["volume"]
        prev = delay(close, 1)
        signed = pd.Series(
            np.where(
                close > prev, vol, np.where(close < prev, -vol, 0.0)
            ),
            index=close.index,
        )
        val = ts_sum(signed, 6).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
