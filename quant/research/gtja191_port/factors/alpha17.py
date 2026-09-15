"""
GTJA191 Alpha17 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(VWAP-MAX(VWAP,15))^DELTA(CLOSE,5)
DolphinDB:
  def gtjaAlpha17(close, vwap){
      return pow(rowRank(vwap - mmax(vwap,15), percent=true), close - mfirst(close,6))
  }

翻译要点:
- vwap - mmax(vwap,15) = VWAP 相对15日最高的折价（负值，越接近高点越接近0）。
- rowRank(…) → rolling pct rank 近似（值域(0,1)）。
- close - mfirst(close,6) = DELTA(close,5)（5日涨跌额），作为指数。
- pow(底, 指数)=逐元素幂：底∈(0,1)，指数为5日涨跌额。
  指数>0（上涨）→ 底缩小；指数<0（下跌）→ 底放大（底<1 的负幂>1）。
- 用 seq_pow 做逐元素幂。

语义: VWAP折价排名的5日涨跌幅幂。上涨日压低折价排名、下跌日放大。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_max, mfirst, seq_pow


class Alpha17Factor(FactorBase):
    name = "gtja_alpha17"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 16:
            return None
        close, vwap = df["close"], df["vwap"]
        base = (vwap - ts_max(vwap, 15)).rolling(15, min_periods=1).rank(pct=True)
        exp = close - mfirst(close, 6)
        val = seq_pow(base, exp).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
