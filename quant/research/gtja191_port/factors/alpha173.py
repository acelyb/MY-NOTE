"""
GTJA191 Alpha173 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: 3*SMA(CLOSE,13,2) - 2*SMA(SMA(CLOSE,13,2),13,2) + SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)
DolphinDB:
  def gtjaAlpha173(close){
      A = ewmMean(close,alpha=2\13)
      B = ewmMean(A,alpha=2\13)
      return 3 * A - 2 * B + ewmMean(B,alpha=2\13)
  }

翻译要点:
- ⚠️ DolphinDB 与研报有偏差：研报第三项为 SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)
  （对 log(close) 做三层 SMA），DolphinDB 第三项为 ewmMean(B,alpha=2/13)
  （对 B=A 的二阶SMA 再做一阶SMA，未取 log）。本移植按 DolphinDB 实现。
- A = SMA(CLOSE,13,2) = ewmMean(alpha=2/13)。
- B = SMA(A,13,2) = ewmMean(alpha=2/13)（对A再平滑）。
- 结果 = 3A - 2B + SMA(B,13,2) = 3A - 2B + ewmMean(B,alpha=2/13)（二阶动量+三阶平滑组合）。
- ewm 理论全历史有效，需足够行数收敛；取 39 行(3*13) 起算。
- log 在 DolphinDB 实现中未使用，故无 log≤0 坑。

语义: 收盘的多层指数平滑组合(3A-2B+C)，三重平滑动量。
      动量向上→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha173Factor(FactorBase):
    name = "gtja_alpha173"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 39:  # 三层 ewm(2/13)，3*13 起算
            return None
        close = df["close"]
        A = sma_recursive(close, 13, 2)           # ewmMean(alpha=2/13)
        B = sma_recursive(A, 13, 2)               # SMA(A,13,2)
        C = sma_recursive(B, 13, 2)               # SMA(B,13,2)
        val = (3 * A - 2 * B + C).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
