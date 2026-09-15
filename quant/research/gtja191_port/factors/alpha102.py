"""
GTJA191 Alpha102 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(MAX(VOLUME-DELAY(VOLUME,1),0),6,1)/SMA(ABS(VOLUME-DELAY(VOLUME,1)),6,1)*100
DolphinDB:
  def gtjaAlpha102(vol){
      A = max((vol-move(vol,1)),0)
      B = abs(vol-move(vol,1))
      return ewmMean(A,alpha=1\6) \ ewmMean(B,alpha=1\6) * 100
  }

翻译要点:
- move(vol,1)=delay(vol,1)。A=max(vol差,0) 上行量；B=|vol差| 总量差。
- SMA(x,6,1)=ewmMean(alpha=1/6)。
- 比值*100 = 6日RSI(成交量版)。B 的 ewm 为0时除零置 NaN。

语义: 成交量RSI(6)。放量上涨占比高→因子大→预期未来收益高（量能动量）。
  与 alpha63/67/79(收盘价RSI) 同族，alpha102 对象是成交量。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ema_mean


class Alpha102Factor(FactorBase):
    name = "gtja_alpha102"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:  # ewm 递归，少量起算
            return None
        vol = df["volume"]
        d = vol - vol.shift(1)   # VOLUME - DELAY(VOLUME,1)
        A = d.clip(lower=0)      # MAX(...,0)
        B = d.abs()              # ABS(...)
        up = ema_mean(A, 1 / 6)
        down = ema_mean(B, 1 / 6)
        val = (up / down.replace(0, np.nan) * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
