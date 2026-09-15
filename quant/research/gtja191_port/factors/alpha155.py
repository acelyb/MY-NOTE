"""
GTJA191 Alpha155 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(VOLUME,13,2)-SMA(VOLUME,27,2)-SMA(SMA(VOLUME,13,2)-SMA(VOLUME,27,2),10,2)
DolphinDB:
  def gtjaAlpha155(vol){
      A = ewmMean(vol,alpha=2\13)
      B = ewmMean(A,alpha=2\27)
      return A - B - ewmMean(A-B,alpha=2\10)
  }

翻译要点:
- ⚠️ DolphinDB 实现与研报公式有偏差：研报 B=SMA(VOL,27,2)，
  DolphinDB B=SMA(A,27,2)（对A再平滑，二次指数加权）。本移植按 DolphinDB 实现，差异注明。
- A = SMA(VOL,13,2) = ewmMean(alpha=2/13)。
- B = SMA(A,27,2) = ewmMean(alpha=2/27)（DolphinDB口径，对A二次平滑）。
- 第三项 = SMA(A-B,10,2) = ewmMean(alpha=2/10)。
- 结果 = A - B - SMA(A-B,10,2)（MACD柱状信号的量能版）。
- ewm 理论全历史有效，需 ≥27 行保证 B 项收敛稳定。

语义: 成交量MACD柱状信号(快线-慢线-信号线)。放量上攻→柱状为正→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha155Factor(FactorBase):
    name = "gtja_alpha155"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 27:  # ewm(2/27) 需足够历史
            return None
        vol = df["volume"]
        A = sma_recursive(vol, 13, 2)    # SMA(VOL,13,2)
        B = sma_recursive(A, 27, 2)      # SMA(A,27,2)（DolphinDB口径）
        diff = A - B
        sig = sma_recursive(diff, 10, 2)  # SMA(A-B,10,2)
        val = (diff - sig).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
