"""
GTJA191 Alpha94 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((CLOSE>DELAY(CLOSE,1)?VOLUME:(CLOSE<DELAY(CLOSE,1)?-VOLUME:0)),30)
DolphinDB:
  def gtjaAlpha94(close, vol){
      return msum(iif(close > mfirst(close, 2), vol, iif(close < mfirst(close, 2), -vol, 0)), 30)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)。涨→+vol，跌→-vol，平→0；过去30日求和。
- 与 alpha84(20日)、alpha43(6日) 同族，仅窗口=30。
- msum=ts_sum；iif 用嵌套 np.where。

语义: 30日量能方向累计(正负量差)。持续上涨放量→因子大→预期未来收益高(动量)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha94Factor(FactorBase):
    name = "gtja_alpha94"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 31:  # delay(1) + sum(30)
            return None
        close, vol = df["close"], df["volume"]
        c_prev = close.shift(1)   # DELAY(CLOSE,1)
        inner = np.where(close > c_prev, vol,
                         np.where(close < c_prev, -vol, 0.0))
        inner = pd.Series(inner, index=close.index)
        val = ts_sum(inner, 30).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
