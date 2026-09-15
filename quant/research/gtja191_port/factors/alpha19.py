"""
GTJA191 Alpha19 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE<DELAY(CLOSE,5)?(CLOSE-DELAY(CLOSE,5))/DELAY(CLOSE,5):
           (CLOSE=DELAY(CLOSE,5)?0:(CLOSE-DELAY(CLOSE,5))/CLOSE))
DolphinDB:
  def gtjaAlpha19(close){
      return iif(close < mfirst(close, 6), (close - mfirst(close, 6)) \ mfirst(close, 6),
             iif(close == mfirst(close, 6), 0, (close - mfirst(close, 6)) \ close))
  }

翻译要点:
- mfirst(close,6)=DELAY(close,5)=delay(close,5)。
- 三分支条件：下跌用 (close-d5)/d5；持平为0；上涨用 (close-d5)/close。
- 即非对称的5日收益：下跌按前值归一，上涨按当值归一（量纲不一，研报设计如此）。
- iif 用 np.where 嵌套实现；除零用 replace(0,np.nan) 规避。
- 无横截面算子，单标的可忠实还原。

语义: 非对称5日收益。上涨与下跌用不同分母归一，放大下跌信号的相对幅度。
  属变形动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay


class Alpha19Factor(FactorBase):
    name = "gtja_alpha19"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # delay(5)+1
            return None
        close = df["close"]
        d5 = delay(close, 5)
        d5_safe = d5.replace(0, np.nan)
        close_safe = close.replace(0, np.nan)
        inner = np.where(close == d5, 0.0, (close - d5) / close_safe)
        val_series = pd.Series(
            np.where(close < d5, (close - d5) / d5_safe, inner),
            index=close.index,
        )
        val = val_series.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
