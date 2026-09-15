"""
GTJA191 Alpha65 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MEAN(CLOSE,6)/CLOSE
DolphinDB:
  def gtjaAlpha65(close){
      return mavg(close, 6) \ close
  }

翻译要点:
- mavg(close,6)=6日收盘均价（MA6）。
- 返回 MA6/CLOSE：>1=收盘价低于6日均线（破位），<1=收盘高于均线。
- 与 alpha66((CLOSE-MA6)/MA6*100) 同源，是线性变换：
    alpha65 = MA6/C = 1/(1 - (C-MA6)/C)；alpha66 = (C-MA6)/MA6*100。
  口径不同（分母为 C vs MA6），分布形态不同。
- 分母（收盘价）为0 实际不可能，无需特别处理。
- 无横截面算子，单标的可忠实还原。

语义: 6日均线/收盘价比。>1=破位下行，<1=高于均线。均线偏离维度。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha65Factor(FactorBase):
    name = "gtja_alpha65"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # mavg(6)
            return None
        close = df["close"]
        ma6 = close.rolling(6).mean()
        val = (ma6 / close).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
