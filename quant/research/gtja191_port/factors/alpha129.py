"""
GTJA191 Alpha129 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((CLOSE-DELAY(CLOSE,1)<0?ABS(CLOSE-DELAY(CLOSE,1)):0),12)
DolphinDB:
  def gtjaAlpha129(close){
      return msum(iif((close - move(close, 1)) < 0, abs(close - move(close, 1)), 0), 12)
  }

翻译要点:
- move(close,1)=delay(close,1)=前一日收盘。
- close-delay1 为负（下跌日）取绝对跌幅，否则记 0。
- msum(...,12)=过去12日下跌日绝对跌幅之和（仅计下跌，上涨日记0）。
- 需 delay(1)+msum(12)=13 行起算。

语义: 12日下跌日绝对跌幅之和。跌幅越大→因子越大。负向波动/下行风险维度，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha129Factor(FactorBase):
    name = "gtja_alpha129"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # delay(1) + msum(12) = 13
            return None
        close = df["close"]
        chg = close - close.shift(1)
        dn = pd.Series(np.where(chg < 0, np.abs(chg), 0.0), index=df.index)
        val = ts_sum(dn, 12).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
