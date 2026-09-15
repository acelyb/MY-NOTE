"""
GTJA191 Alpha185 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK((-1 * ((1 - (OPEN / CLOSE))^2)))
DolphinDB:
  def gtjaAlpha185(open, close){
      return rowRank(-1 * pow(1 - open \ close, 2), percent=true)
  }

翻译要点:
- open/close 为开收比；1 - open/close = 开收相对偏离（open<close 为正，open>close 为负）。
- pow(.,2) 平方后恒非负；-1* 取负 → 值域 (-inf, 0]。
- rowRank 横截面排名 → rolling(10) 时序 pct rank 近似（含前导NaN用 min_periods=1）。
- 除零：close=0 时 open/close→inf，1-inf=-inf，平方→inf，取负→-inf；用 replace 守卫。
- pow 底数可能为负（open>close 时 1-ratio<0），指数为整数2，无负底数非整数指数坑。
- 最长链 rolling_rank(10) = 10 行起算。

语义: 当日"开收偏离平方"取负后的时序排名。
      开收偏离大→取负后小→排名小→因子小；偏离小→因子大。
      日内反转维度，方向以 IC 实测定。含一层横截面 rowRank 近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha185Factor(FactorBase):
    name = "gtja_alpha185"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # rolling_rank(10)
            return None
        op, close = df["open"], df["close"]
        ratio = op / close.replace(0, np.nan)
        inner = -1 * (1 - ratio) ** 2
        val = inner.rolling(10, min_periods=1).rank(pct=True).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
