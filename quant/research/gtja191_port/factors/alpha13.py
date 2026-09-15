"""
GTJA191 Alpha13 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (((HIGH*LOW)^0.5) - VWAP)   [stateless]
DolphinDB:
  def gtjaAlpha13(high, low, vwap){
      return pow((high*low),0.5) - vwap
  }

翻译要点:
- (HIGH*LOW)^0.5 = 高低价几何均值，近似当日价格中枢。
- 几何均值 - VWAP：VWAP 高于几何中枢→负（尾盘拉高/放量高价成交）；低于→正。
- 无横截面算子，单标的可忠实还原（stateless，当日值）。

语义: 高低价几何均值与 VWAP 之差。正→当日 VWAP 偏低（成交重心偏低）；方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha13Factor(FactorBase):
    name = "gtja_alpha13"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 1:
            return None
        high, low, vwap = df["high"], df["low"], df["vwap"]
        val = ((high * low) ** 0.5 - vwap).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
