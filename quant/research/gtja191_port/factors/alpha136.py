"""
GTJA191 Alpha136 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((-1 * RANK(DELTA(RET, 3))) * CORR(OPEN, VOLUME, 10))
DolphinDB:
  def gtjaAlpha136(open, close, vol){
      return -1 * rowRank(ratios(close) - 1 - mfirst(ratios(close) - 1, 4), percent=true) * mcorr(open, vol, 10)
  }

翻译要点:
- ratios(close)-1 = ret = 日收益率。
- mfirst(ret,4)=delay(ret,3)=3日前收益率；delta(ret,3)=ret-delay(ret,3)。
- rowRank 横截面排名 → rolling 时序 pct rank 近似（有损），含前导NaN用 min_periods=1。
- mcorr(open,vol,10)=10日(开盘,量)时序相关。
- 取负。最长链 ret(需1)+delay(3)+rank滚动+corr(10) ≈ 14 行起算。

语义: "收益率3日变化排名" × "开盘量10日相关"，取负。
      收益率动量变化与开盘量价同向的交叉维度，方向以 IC 实测定。
      含一层横截面 rowRank 近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_corr


class Alpha136Factor(FactorBase):
    name = "gtja_alpha136"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 14:  # ret(1) + delay(3) + corr(10) = 14
            return None
        op, close, vol = df["open"], df["close"], df["volume"]
        r = close.pct_change()            # RET
        dret3 = r - r.shift(3)            # DELTA(RET,3)
        r_rank = dret3.rolling(10, min_periods=1).rank(pct=True)  # RANK 近似
        corr_ov = ts_corr(op, vol, 10)    # CORR(OPEN,VOL,10)
        val = (-r_rank * corr_ov).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
