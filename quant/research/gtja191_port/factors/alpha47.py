"""
GTJA191 Alpha47 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((TSMAX(HIGH,6)-CLOSE)/(TSMAX(HIGH,6)-TSMIN(LOW,6))*100, 9, 1)
DolphinDB:
  def gtjaAlpha47(close, high, low){
      A = (mmax(high,6)-close)\\(mmax(high,6)-mmin(low,6))*100
      return ewmMean(A, alpha=1\\9)
  }

翻译要点:
- TSMAX(HIGH,6)=过去6日最高价的最高（mmax）；TSMIN(LOW,6)=过去6日最低价的最低（mmin）
- A = (6日最高-当日收)/(6日最高-6日最低)*100 —— 当日收盘在6日高低区间的相对位置（越接近6日最高→A越小=越强）
- SMA(A,9,1)=研报递归指数加权 Y_t=(A_{t-1}*1+Y_{t-1}*8)/9，等价 EWM(alpha=1/9, adjust=False)
  DolphinDB 用 ewmMean(alpha=1/9) 即此。

方向: A 越小（收盘越接近6日高点）→ 因子越小。"值越大越好"需实测定方向，
  公式无显式取负，故原始方向=收盘越弱(离高点远)因子越大→可能是反向因子。IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive, ts_max, ts_min


class Alpha47Factor(FactorBase):
    name = "gtja_alpha47"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:
            return None
        high, low, close = df["high"], df["low"], df["close"]
        hh6 = ts_max(high, 6)   # TSMAX(HIGH,6)
        ll6 = ts_min(low, 6)    # TSMIN(LOW,6)
        denom = hh6 - ll6
        a = (hh6 - close) / denom.replace(0, pd.NA) * 100
        sma = sma_recursive(a, 9, 1)  # SMA(A,9,1)
        val = sma.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
