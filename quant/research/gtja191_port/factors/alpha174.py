"""
GTJA191 Alpha174 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)
DolphinDB:
  def gtjaAlpha174(close){
      A = iif(close>move(close,1),mstd(close,20),0)
      return ewmMean(A,alpha=1\20)
  }

翻译要点:
- move(close,1)=delay(close,1)=前日收盘。
- iif(close>dc1, mstd(close,20), 0): 上涨日取20日收盘标准差，下跌日记0。
- SMA(A,20,1)=ewmMean(alpha=1/20) 递归指数加权均值。
- 即"上涨日波动率的指数平滑"（与 alpha160 下跌日版互补）。
- 最长链：mstd(20)+ewm(20 理论全历史) ≈ 20 行起算。

语义: 上涨日20日波动的指数平滑均值。上涨且波动大→因子大，
      正向风险维度（上涨波动），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive, ts_std


class Alpha174Factor(FactorBase):
    name = "gtja_alpha174"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mstd(20) + ewm
            return None
        close = df["close"]
        dc1 = close.shift(1)                          # DELAY(CLOSE,1)
        std20 = ts_std(close, 20)                      # STD(CLOSE,20)
        A = pd.Series(np.where(close > dc1, std20, 0.0), index=df.index)
        val = sma_recursive(A, 20, 1).iloc[-1]        # SMA(A,20,1)
        if pd.isna(val):
            return None
        return float(val)
