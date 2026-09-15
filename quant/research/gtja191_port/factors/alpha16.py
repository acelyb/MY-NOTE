"""
GTJA191 Alpha16 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK(CORR(RANK(VOLUME),RANK(VWAP),5))，外层取过去5日最大
DolphinDB:
  def gtjaAlpha16(vol, vwap){
      return -1 * mmax(rowRank(mcorr(rowRank(vol,percent=true), rowRank(vwap,percent=true), 5), percent=true), 5)
  }

翻译要点:
- 内层 rowRank(vol)/rowRank(vwap) → rolling pct rank 近似。
- mcorr(量排名, VWAP排名, 5) = 过去5日两者时序相关。
- 外层 rowRank(…,percent=true) 再排名，再 mmax(…,5) 取过去5日最大。
- 整体取负。

语义: 量-VWAP 排名相关的5日时序相关，取5日最大后取负。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_max


class Alpha16Factor(FactorBase):
    name = "gtja_alpha16"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:
            return None
        vol, vwap = df["volume"], df["vwap"]
        rv = vol.rolling(5, min_periods=1).rank(pct=True)
        rvw = vwap.rolling(5, min_periods=1).rank(pct=True)
        corr5 = ts_corr(rv, rvw, 5)
        r_corr = corr5.rolling(5, min_periods=1).rank(pct=True)
        val = (-ts_max(r_corr, 5)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
