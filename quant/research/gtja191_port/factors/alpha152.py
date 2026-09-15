"""
GTJA191 Alpha152 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SMA(MEAN(DELAY(SMA(DELAY(CLOSE/DELAY(CLOSE,9),1),9,1),1),12)
     -MEAN(DELAY(SMA(DELAY(CLOSE/DELAY(CLOSE,9),1),9,1),1),26), 9,1)
DolphinDB:
  def gtjaAlpha152(close){
      A = ewmMean(move((close\move(close,9)),1),alpha=1\9)
      B = mavg(move(A,1),12)-mavg(move(A,1),26)
      return ewmMean(B,alpha=1\9)
  }

翻译要点:
- 内层: close/move(close,9)=close/delay(close,9) (9日收盘价比)；
  move(...,1)=delay(.,1)；ewmMean(alpha=1/9)=SMA(.,9,1)。记为 A。
- B = MEAN(DELAY(A,1),12) - MEAN(DELAY(A,1),26) = 12日-26日 A 的双均线差(MACD差)。
- 结果 = SMA(B,9,1) = ewmMean(B, alpha=1/9)。
- 最长链: delay(9)+delay(1)+ewm(9 理论全历史) + delay(1)+mavg(26) + ewm(9) ≈ 37 行起算。

语义: 收盘9日价比经SMA平滑后的12-26双均线差再SMA(嵌套MACD类动量)。
      动量向上→因子大→预期未来收益高，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha152Factor(FactorBase):
    name = "gtja_alpha152"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 37:  # delay(9)+delay(1)+mavg(26)+ewm
            return None
        close = df["close"]
        ratio9 = close / close.shift(9)                # CLOSE/DELAY(CLOSE,9)
        d_ratio = ratio9.shift(1)                      # DELAY(...,1)
        A = sma_recursive(d_ratio, 9, 1)               # SMA(.,9,1) = ewmMean(alpha=1/9)
        dA = A.shift(1)                                # DELAY(A,1)
        B = dA.rolling(12).mean() - dA.rolling(26).mean()
        val = sma_recursive(B, 9, 1).iloc[-1]          # SMA(B,9,1)
        if pd.isna(val):
            return None
        return float(val)
