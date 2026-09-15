"""
GTJA191 Alpha66 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)*100
DolphinDB:
  def gtjaAlpha66(close){
      return (close - mavg(close, 6)) \ mavg(close, 6) * 100
  }

翻译要点:
- mavg(close,6)=6日收盘均价 MA6。
- 返回 (CLOSE-MA6)/MA6*100 = 收盘相对6日均线的偏离百分比。
- 与 alpha65(MA6/CLOSE) 同源但分母不同：alpha66 分母为 MA6，alpha65 分母为 CLOSE。
  alpha66 是标准的"价格-均线乖离率 (BIAS)"形式。
- 与 alpha71((CLOSE-MA24)/MA24*100) 同源，窗口不同（6 vs 24）。
- 分母为0实际不可能，无需特别处理。
- 无横截面算子，单标的可忠实还原。

语义: 6日 BIAS（乖离率）。正值=收盘高于均线，负值=低于均线。
  均线回归类因子常用法是极端值看反转，方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha66Factor(FactorBase):
    name = "gtja_alpha66"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # mavg(6)
            return None
        close = df["close"]
        ma6 = close.rolling(6).mean()
        val = ((close - ma6) / ma6 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
