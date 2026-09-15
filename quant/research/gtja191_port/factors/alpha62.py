"""
GTJA191 Alpha62 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * CORR(HIGH, RANK(VOLUME), 5)
DolphinDB:
  def gtjaAlpha62(high, vol){
      return -1 * mcorr(high, rowRank(vol, percent=true), 5)
  }

翻译要点:
- rowRank(vol, percent=true)：成交量的横截面排名。单标的用 rolling(5) 时序 pct rank 近似。
- mcorr(high, 量排名, 5)=过去5日(高价 vs 量排名)的时序相关。
- 整体取负。
- 与 alpha5(-TSMAX(CORR(量rank,高价rank,5),3)) 不同：alpha62 是"高价(原值) vs 量排名"的5日相关，
  alpha5 是"量排名 vs 高价排名"相关的3日峰值。两者量价相关但口径不同。

语义: 高价与量排名的5日时序相关，取负。
  高价创新高且放量→相关高→取负后小→预期未来收益低（高位放量反转）。
  含一层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha62Factor(FactorBase):
    name = "gtja_alpha62"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # rank(5) + corr(5)
            return None
        high, vol = df["high"], df["volume"]
        rv = vol.rolling(5).rank(pct=True)
        corr5 = high.rolling(5).corr(rv)
        val = (-corr5).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
