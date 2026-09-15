"""
GTJA191 Alpha127 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (MEAN((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2))^(1/2)
DolphinDB:
  def gtjaAlpha127(close){
      return pow(mavg(pow(100 * (close - max(close, 12)) \ max(close, 12), 2),12), 0.5)
  }

翻译要点:
- max(close,12)=ts_max(close,12)=过去12日收盘最高。
- 100*(close-ts_max12)/ts_max12 = 收盘相对12日高点的偏离(%)，为负或零。
- 平方后取12日均值(msum/12)再开根号 = 12日均方根偏离度。
- mavg(pow(...,2),12) 需先有 ts_max(12) 再 mavg(12)，共 23 行起算。
- 除零：ts_max(close,12) 为 0 时置 NaN。

语义: 收盘相对12日高点的均方根偏离度。收盘持续接近高点→偏离小→因子小；
      收盘远低于高点→偏离大→因子大。超买/超卖类反转，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_max, ts_mean


class Alpha127Factor(FactorBase):
    name = "gtja_alpha127"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 23:  # ts_max(12) + ts_mean(12) = 23
            return None
        close = df["close"]
        mx = ts_max(close, 12)
        dev = 100 * (close - mx) / mx.replace(0, np.nan)
        sq = dev ** 2
        rms = ts_mean(sq, 12) ** 0.5
        val = rms.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
