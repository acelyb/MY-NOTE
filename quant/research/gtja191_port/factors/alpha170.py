"""
GTJA191 Alpha170 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(1/CLOSE)*VOL/MEAN(VOL,20)*HIGH*RANK(HIGH-CLOSE)/(SUM(HIGH,5)/5) - RANK(VWAP-DELAY(VWAP,5))
DolphinDB:
  def gtjaAlpha170(close, high, vol, vwap){
      return rowRank(1\close, percent=true) * vol \ mavg(vol,20) * high * rowRank(high-close, percent=true) \ (msum(high,5)\5) - rowRank(vwap-mfirst(vwap,6), percent=true)
  }

翻译要点:
- 第一大项：rowRank(1/close)=价格倒数排名（低价股排名高）；vol/mavg(vol,20)=量比；
  ×high×rowRank(high-close)=上影线排名；÷(5日高价均)。
  = 价格倒数排名 × 量比 × 高价 × 上影排名 / 5日高价均。
- 第二项：rowRank(vwap-mfirst(vwap,6))=5日VWAP变化排名。
- 整体 = 第一大项 - 第二项。含多层 rank 近似（有损）。

语义: 低价+放量+上影的联合强度 - VWAP变化排名。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_mean, ts_sum, mfirst


class Alpha170Factor(FactorBase):
    name = "gtja_alpha170"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        close, high, vol, vwap = df["close"], df["high"], df["volume"], df["vwap"]
        r_inv = (1 / close).rolling(20, min_periods=1).rank(pct=True)
        vol_ratio = vol / ts_mean(vol, 20).replace(0, pd.NA)
        r_shadow = (high - close).rolling(20, min_periods=1).rank(pct=True)
        high5 = ts_sum(high, 5) / 5
        term1 = r_inv * vol_ratio * high * r_shadow / high5.replace(0, pd.NA)
        term2 = (vwap - mfirst(vwap, 6)).rolling(20, min_periods=1).rank(pct=True)
        val = (term1 - term2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
