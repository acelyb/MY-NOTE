"""
GTJA191 Alpha132 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(AMOUNT,20)，AMOUNT=VOL*VWAP
DolphinDB:
  def gtjaAlpha132(vol, vwap){
      return mavg(vol * vwap, 20)
  }

翻译要点:
- vol*vwap=成交额代理；mavg(...,20)=20日均值。

语义: 20日平均成交额代理（中期流动性水平）。无横截面 rank，单标的可忠实还原。
  注意：与 alpha150(典型价×量) 同属流动性/规模代理，IC 强可能源于规模效应，需相关性诊断警惕。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_mean


class Alpha132Factor(FactorBase):
    name = "gtja_alpha132"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        vol, vwap = df["volume"], df["vwap"]
        amt = vol * vwap
        val = ts_mean(amt, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
