"""
GTJA191 Alpha70 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: STD(AMOUNT,6)，其中 AMOUNT = VOL*VWAP（成交额代理）
DolphinDB:
  def gtjaAlpha70(vol, vwap){
      return mstd(vol * vwap, 6)
  }

翻译要点:
- vol*vwap = 成交额代理（量×均价，近似当日成交额）。
- mstd(...,6)=过去6日成交额代理的标准差（流动性/活跃度波动）。

语义: 6日成交额代理波动率。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_std


class Alpha70Factor(FactorBase):
    name = "gtja_alpha70"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 7:
            return None
        vol, vwap = df["volume"], df["vwap"]
        amt = vol * vwap
        val = ts_std(amt, 6).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
