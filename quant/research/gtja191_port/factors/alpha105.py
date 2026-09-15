"""
GTJA191 Alpha105 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * CORR(RANK(OPEN), RANK(VOLUME), 10)
DolphinDB:
  def gtjaAlpha105(open, vol){
      return -1 * mcorr(rowRank(open, percent=true), rowRank(vol, percent=true), 10)
  }

翻译要点:
- rowRank(open)/rowRank(vol) 横截面排名 → rolling(10) 时序 pct rank 近似。
- mcorr(开盘排名, 量排名, 10)=过去10日两者的时序相关。
- 整体取负。
- 与 alpha1(量变化×日内收益相关) 不同：alpha105 是"开盘价排名 vs 量排名"的10日相关，
  强调开盘价水平与量级的同步性（开盘跳空放量等）。

语义: 开盘价排名与量排名的10日时序相关，取负。
  开盘高开且放量→相关高→取负后小→预期未来收益低。
  量价相关维度，用开盘价而非收盘/高价。含两层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha105Factor(FactorBase):
    name = "gtja_alpha105"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # rank(10) + corr(10)
            return None
        op, vol = df["open"], df["volume"]
        ro = op.rolling(10).rank(pct=True)
        rv = vol.rolling(10).rank(pct=True)
        corr10 = ro.rolling(10).corr(rv)
        val = (-corr10).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
