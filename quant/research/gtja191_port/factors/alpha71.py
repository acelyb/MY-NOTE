"""
GTJA191 Alpha71 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-MEAN(CLOSE,24))/MEAN(CLOSE,24)*100
DolphinDB:
  def gtjaAlpha71(close){
      return (close - mavg(close, 24)) \ mavg(close, 24) * 100
  }

翻译要点:
- mavg(close,24)=24日收盘均价 MA24。
- 返回 (CLOSE-MA24)/MA24*100 = 24日 BIAS（乖离率）。
- 与 alpha66（6日 BIAS）同源，窗口不同。
- 分母为0实际不可能，无需特别处理。
- 无横截面算子，单标的可忠实还原。

语义: 24日 BIAS（乖离率）。正值=收盘高于24日均线，负值=低于均线。
  中期均线回归维度，比 alpha66(6日) 更慢。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha71Factor(FactorBase):
    name = "gtja_alpha71"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # mavg(24)
            return None
        close = df["close"]
        ma24 = close.rolling(24).mean()
        val = ((close - ma24) / ma24 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
