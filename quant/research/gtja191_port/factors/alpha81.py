"""
GTJA191 Alpha81 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(VOLUME,21,2)
DolphinDB:
  def gtjaAlpha81(vol){
      return ewmMean(vol, alpha=1\21)
  }

翻译要点:
- SMA(VOLUME,21,2)=研报递归指数加权，Y_t = (VOL_{t-1}*2 + Y_{t-1}*(21-2))/21，
  alpha=m/n=2/21，对应 ewmMean(alpha=2/21)。
- ⚠️ DolphinDB 用 ewmMean(alpha=1/21) 而非 2/21，与研报公式 SMA(21,2) 不一致
  （DolphinDB 写 alpha=1\21，可能笔误或口径差异）。本实现按研报公式 SMA(21,2) 用 alpha=2/21
  （sma_recursive(vol,21,2)），与 base.py 的研报口径一致；差异在 docstring 注明。
  若需严格对齐 DolphinDB，改用 ema_mean(vol, 1/21)。
- 无横截面算子，单标的可忠实还原。

语义: 成交量的21日指数平滑（研报 SMA(21,2) 口径）。
  反映中期成交量水平，平滑掉短期波动。纯量能水平维度。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha81Factor(FactorBase):
    name = "gtja_alpha81"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:  # ewm 递归至少需1个有效值
            return None
        vol = df["volume"]
        sma = sma_recursive(vol, 21, 2)  # 研报 SMA(21,2): alpha=2/21
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
