"""
GTJA191 Alpha171 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((-1 * ((LOW - CLOSE) * (OPEN^5))) / ((CLOSE - HIGH) * (CLOSE^5)))
DolphinDB:
  def gtjaAlpha171(open, close, high, low){
      return -1 * (low - close) * pow(open, 5) \ ((close - high) * pow(close, 5))
  }

翻译要点:
- 无窗口，当日四价组合。
- 分子: -1*(low-close)*open^5 = (close-low)*open^5（下影×开盘^5）。
- 分母: (close-high)*close^5（上影负值×收盘^5，close-high≤0）。
- 整体 = (close-low)*open^5 / ((close-high)*close^5)。
- 除零：close=high 时分母=0 置 NaN；close=0 时 pow(close,5)=0 置 NaN。
- pow(open/close,5) 整数指数，无负底数非整数指数坑。
- 需 1 行。

语义: 下影×开盘^5 与 上影×收盘^5 的比率。
      下影长且开盘高、上影短且收盘高 → 因子大 → 预期未来收益高（下影支撑+收强），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha171Factor(FactorBase):
    name = "gtja_alpha171"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 1:
            return None
        op, close, high, low = df["open"], df["close"], df["high"], df["low"]
        num = -1 * (low - close) * (op ** 5)
        den = ((close - high) * (close ** 5)).replace(0, np.nan)
        val = (num / den).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
