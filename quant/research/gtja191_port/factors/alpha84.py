"""
GTJA191 Alpha84 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(IF(CLOSE>DELAY(CLOSE,1), VOLUME, IF(CLOSE<DELAY(CLOSE,1), -VOLUME, 0)), 20)
DolphinDB:
  def gtjaAlpha84(close, vol){
      return msum(iif(close > mfirst(close, 2), vol, iif(close < mfirst(close, 2), -vol, 0)), 20)
  }

翻译要点:
- mfirst(close,2)=昨收 close_{t-1}
- 上涨日 +量，下跌日 -量，平日 0；过去20日带符号量累加。
- 无横截面算子，单标的可忠实还原。

语义: 20日"带方向的成交量"累积——上涨日加量、下跌日减量。
  本质是量价的 OBV(On-Balance Volume) 类指标：价涨量+、价跌量-，净累积看多空力量。
  与 alpha40(上涨/下跌量比) 互补：alpha84 是净额，alpha40 是比值。
  方向 IC 定夺（净量正=上涨放量主导）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha84Factor(FactorBase):
    name = "gtja_alpha84"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        close, vol = df["close"], df["volume"]
        prev = close.shift(1)
        import numpy as np
        signed = pd.Series(
            np.where((close > prev).values, vol.values, np.where((close < prev).values, -vol.values, 0.0)),
            index=close.index,
        )
        signed = pd.to_numeric(signed, errors="coerce")
        val = signed.rolling(20).sum().iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
