"""
GTJA191 Alpha96 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(SMA((CLOSE-TSMIN(LOW,9))/(TSMAX(HIGH,9)-TSMIN(LOW,9))*100,3,1),3,1)
DolphinDB:
  def gtjaAlpha96(close, high, low){
      A = (close - mmin(low,9))\(mmax(high,9) - mmin(low,9))*100
      B = ewmMean(A,alpha=1\3)
      return ewmMean(B,alpha=1\3)
  }

翻译要点:
- A = (close - ts_min(low,9)) / (ts_max(high,9) - ts_min(low,9)) * 100
  = 收盘在9日高低区间的位置(0~100)，类似 KDJ/K 值。
- B = SMA(A,3,1)=ewmMean(alpha=1/3)；输出 = SMA(B,3,1)=ewmMean(alpha=1/3)（二次平滑）。
- 分母 (ts_max-ts_min)=0 时除零置 NaN。

语义: 9日区间位置的二次指数平滑(类 KDJ 的双重平滑 K)。
  收盘接近9日高点→A 大→因子大→预期未来收益高（动量）。
  与 alpha57(单次平滑) 同族，alpha96 多一次平滑，更钝化。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ema_mean, ts_max, ts_min


class Alpha96Factor(FactorBase):
    name = "gtja_alpha96"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:  # ts_max/ts_min(9)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        hh = ts_max(high, 9)
        ll = ts_min(low, 9)
        A = (close - ll) / (hh - ll).replace(0, np.nan) * 100
        B = ema_mean(A, 1 / 3)          # SMA(A,3,1)
        out = ema_mean(B, 1 / 3)        # SMA(B,3,1)
        val = out.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
