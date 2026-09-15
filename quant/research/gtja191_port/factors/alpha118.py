"""
GTJA191 Alpha118 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100
DolphinDB:
  def gtjaAlpha118(open, high, low){
      return msum(high - open, 20) \ msum(open - low, 20) * 100
  }

翻译要点:
- 分子 = 过去20日 (high - open) 累计 = 日内上影幅度累计（开低于高）。
- 分母 = 过去20日 (open - low) 累计 = 日内下影幅度累计（开高于低）。
- 比值*100，分母为0时除零置 NaN。
- msum=ts_sum。

语义: 20日上影幅度/下影幅度*100。多方上攻占优→因子大→预期未来收益高。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha118Factor(FactorBase):
    name = "gtja_alpha118"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # sum(20) 需要 20 行
            return None
        op, high, low = df["open"], df["high"], df["low"]
        up = ts_sum(high - op, 20)     # SUM(HIGH-OPEN,20)
        down = ts_sum(op - low, 20)    # SUM(OPEN-LOW,20)
        val = (up / down.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
