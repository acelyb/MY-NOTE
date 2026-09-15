"""
GTJA191 Alpha95 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: STD(AMOUNT,20)，AMOUNT=VOL*VWAP
DolphinDB:
  def gtjaAlpha95(vol, vwap){
      return mstd(vol * vwap, 20)
  }

翻译要点:
- vol*vwap = 成交额代理；mstd(...,20)=20日成交额代理标准差。

语义: 20日成交额代理波动率（中期流动性波动）。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_std


class Alpha95Factor(FactorBase):
    name = "gtja_alpha95"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        vol, vwap = df["volume"], df["vwap"]
        amt = vol * vwap
        val = ts_std(amt, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
