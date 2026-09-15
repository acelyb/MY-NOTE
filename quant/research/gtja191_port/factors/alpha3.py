"""
GTJA191 Alpha3 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SUM(IF(CLOSE==DELAY(CLOSE,1), 0, CLOSE-IF(CLOSE>DELAY(CLOSE,1), MIN(LOW,DELAY(CLOSE,1)), MAX(HIGH,DELAY(CLOSE,1)))), 6)
DolphinDB:
  def gtjaAlpha3(close, high, low){
      tmp = iif(close > mfirst(close, 2), min(low, mfirst(close, 2)), max(high, mfirst(close, 2)))
      return msum(iif(close == mfirst(close, 2), 0, close - tmp), 6)
  }

翻译要点:
- mfirst(close,2)=昨收 C_{t-1}。
- tmp: 若今日上涨(C>C1)，取 MIN(LOW, C1)（昨收与今日低价的较小者，作为支撑锚）；
       否则取 MAX(HIGH, C1)（昨收与今日高价的较大者，作为阻力锚）。
- close - tmp: 上涨日取 收盘-支撑(突破支撑的距离)；下跌/平 取 收盘-阻力(跌破阻力的负距离)。
- 若 C==C1（平收）记0。
- 过去6日累加。

语义: 6日内"相对锚点(支撑/阻力)突破距离"的累加。
  上涨日累加突破支撑的幅度，下跌日累加跌破阻力的负幅度 → 净趋势动能。
  与 momentum(纯涨跌幅) 不同：alpha3 以昨收为锚、用当日高低做支撑/阻力，是"突破型"动量。
  无横截面算子，单标的可忠实还原。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha3Factor(FactorBase):
    name = "gtja_alpha3"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:  # mfirst(2) + msum(6)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        c1 = close.shift(1)
        # tmp: 上涨取 min(low,c1)，否则取 max(high,c1)
        tmp = pd.Series(
            np.where((close > c1).values, np.minimum(low.values, c1.values),
                     np.maximum(high.values, c1.values)),
            index=close.index,
        )
        contrib = pd.Series(
            np.where((close == c1).values, 0.0, (close - tmp).values),
            index=close.index,
        )
        val = contrib.rolling(6).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
