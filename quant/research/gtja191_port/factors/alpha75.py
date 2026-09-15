"""
GTJA191 Alpha75 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: COUNT(CLOSE>OPEN AND INDEX_CLOSE<INDEX_OPEN, 50) / COUNT(INDEX_CLOSE<INDEX_OPEN, 50)
DolphinDB:
  def gtjaAlpha75(open, close, index_open, index_close){
      return mcount(iif(close>open,1,0) * iif(index_close<index_open,1,0), 50) \ mcount(iif(index_close<index_open,1,0), 50)
  }

翻译要点:
- 个股上涨日(close>open) 且 指数下跌日(index_close<index_open) 同时成立 → 计数。
- mcount(共动日, 50) / mcount(指数下跌日, 50) = 过去50日"指数跌但个股涨"的条件概率。
- 反向 beta 口径：个股对市场下跌的独立性（抗跌/逆市上涨能力）。
- 分母可能0（50日指数全涨），需防护。

语义: 50日内指数下跌日中个股上涨的比例（逆市上涨概率）。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha75Factor(FactorBase):
    name = "gtja_alpha75"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 51:
            return None
        op, close = df["open"], df["close"]
        io, ic = df["index_open"], df["index_close"]
        up = (close > op).astype("float64")
        idx_down = (ic < io).astype("float64")
        both = up * idx_down
        num = both.rolling(50).sum()
        den = idx_down.rolling(50).sum()
        val = (num / den.replace(0, pd.NA)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
