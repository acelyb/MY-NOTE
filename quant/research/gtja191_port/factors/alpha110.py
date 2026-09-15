"""
GTJA191 Alpha110 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100
DolphinDB:
  def gtjaAlpha110(close, high, low){
      return msum(max(0, high - mfirst(close, 2)), 20) \ msum(max(0, mfirst(close, 2) - low), 20) * 100
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=昨收。
- 分子 = 20日 max(0, high - 昨收) 累计 = 向上跳空幅度累计。
- 分母 = 20日 max(0, 昨收 - low) 累计 = 向下跳空幅度累计。
- 比值*100，分母为0时除零置 NaN。
- msum=ts_sum；max(0,x)=np.maximum(0,x)。

语义: 20日向上跳空幅度/向下跳空幅度*100。多方跳空占优→因子大→预期未来收益高。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha110Factor(FactorBase):
    name = "gtja_alpha110"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(1) + sum(20)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        c_prev = close.shift(1)   # DELAY(CLOSE,1)
        up = np.maximum(0.0, high - c_prev)
        down = np.maximum(0.0, c_prev - low)
        s_up = ts_sum(pd.Series(up, index=close.index), 20)
        s_down = ts_sum(pd.Series(down, index=close.index), 20)
        val = (s_up / s_down.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
