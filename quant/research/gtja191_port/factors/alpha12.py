"""
GTJA191 Alpha12 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK((OPEN-(SUM(VWAP,10)/10)))) * (-1*(RANK(ABS((CLOSE-VWAP)))))
DolphinDB:
  def gtjaAlpha12(open, close, vwap){
      return rowRank(open - msum(vwap,10)\10, percent=true) * (-1 * rowRank(abs(close-vwap), percent=true))
  }

翻译要点:
- msum(vwap,10)/10 = 过去10日 VWAP 均值。
- open - 均值 = 开盘价相对近期 VWAP 偏离。
- abs(close-vwap) = 当日收盘与 VWAP 绝对偏离（VWAP-CLOSE 偏离强度，核心 alpha 信号）。
- 两层 rowRank，第二项取负 → 开盘高于近期均价且收盘大幅偏离 VWAP 时取负变小。

语义: 开盘价相对10日均VWAP偏离排名 × 收盘VWAP绝对偏离排名(取负)。
  含两层横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_sum


class Alpha12Factor(FactorBase):
    name = "gtja_alpha12"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 11:
            return None
        op, close, vwap = df["open"], df["close"], df["vwap"]
        r1 = (op - ts_sum(vwap, 10) / 10).rolling(10, min_periods=1).rank(pct=True)
        r2 = (close - vwap).abs().rolling(10, min_periods=1).rank(pct=True)
        val = (r1 * (-1 * r2)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
