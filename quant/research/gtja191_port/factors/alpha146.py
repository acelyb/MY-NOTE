"""
GTJA191 Alpha146 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  MEAN((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1) - SMA((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1),61,2), 20)
  * ((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1) - SMA((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1),61,2))
  / SMA(((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1) - ((CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1) - SMA(...,61,2)))^2, 60)
DolphinDB:
  def gtjaAlpha146(close){
      A = (close-move(close,1))\move(close,1)
      B = ewmMean(A,alpha=2\61)
      return mavg((A - B),20) \ mavg(pow(B,2),60)
  }

翻译要点:
- A = 日收益率 ret = close/delay(close,1)-1。
- B = SMA(A,61,2) = ewmMean(alpha=2/61) 递归指数加权均值（研报 SMA(n,m) → alpha=m/n）。
- 分子 = MEAN(A-B, 20) = 20日 (收益-其SMA) 均值 = 20日动量偏差均值。
- 分母 = MEAN(B^2, 60) = 60日 B 的均方。
- ⚠️ DolphinDB 分母用 pow(B,2)（B的平方），但研报公式写的是 (A-(A-B))^2 = B^2，与 DolphinDB 一致。
  B 可能为负，指数为整数2，B**2 无负底数非整数指数坑。
- 除零：分母均方为 0 时置 NaN。
- 最长链：ewm(alpha=2/61) 理论全历史有效，但 mavg(60) 需 60 行；ret 需 delay(1)。

语义: 动量偏差的20日均值除以SMA的60日均方(标准化动量)。
      动量为正且持续→分子大→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha146Factor(FactorBase):
    name = "gtja_alpha146"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 61:  # ewm(2/61) + mavg(60)
            return None
        close = df["close"]
        A = close.pct_change()                    # (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)
        B = sma_recursive(A, 61, 2)               # SMA(A,61,2) = ewmMean(alpha=2/61)
        num = (A - B).rolling(20).mean()          # MEAN(A-B,20)
        den = (B ** 2).rolling(60).mean()         # MEAN(B^2,60)
        val = (num / den.replace(0, np.nan)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
