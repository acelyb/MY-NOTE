"""
GTJA191 Alpha114 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(DELAY((HIGH-LOW)/(SUM(CLOSE,5)/5),3)) * RANK(RANK(VOL)) / ((HIGH-LOW)/(SUM(CLOSE,5)/5)/(VWAP-CLOSE))
DolphinDB:
  def gtjaAlpha114(close, high, low, vol, vwap){
      return rowRank(mfirst((high-low)\(msum(close,5)\5), 3), percent=true) * rowRank(rowRank(vol,percent=true), percent=true) \ ((high-low)\(msum(close,5)\5) \ (vwap-close))
  }

翻译要点:
- spread=(high-low)/(msum(close,5)/5)=日内振幅率（相对5日均价）。
- 第一项：mfirst(spread,3)=delay(spread,2)（2日前振幅率）；rowRank 排名。
- 第二项：rowRank(rowRank(vol))=对量排名再排名（双层 rank）；rowRank 排名。
- 分母：spread/(vwap-close)；vwap-close=VWAP偏离收盘。
- 整体 = 第一项 × 第二项 / 分母。分母0需防护（vwap=close时）。

语义: 滞后振幅率排名 × 量双层排名 / (振幅率/VWAP偏离)。多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_sum, mfirst


class Alpha114Factor(FactorBase):
    name = "gtja_alpha114"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 8:
            return None
        close, high, low, vol, vwap = df["close"], df["high"], df["low"], df["volume"], df["vwap"]
        spread = (high - low) / (ts_sum(close, 5) / 5)
        r1 = mfirst(spread, 3).rolling(8, min_periods=1).rank(pct=True)
        rv = vol.rolling(8, min_periods=1).rank(pct=True)
        r2 = rv.rolling(8, min_periods=1).rank(pct=True)
        denom = spread / (vwap - close).replace(0, pd.NA)
        val = (r1 * r2 / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
