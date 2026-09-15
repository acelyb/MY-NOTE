"""
GTJA191 Alpha148 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((RANK(CORR(OPEN, SUM(MEAN(VOLUME,60),9), 6)) < RANK((OPEN - TSMIN(OPEN,14)))) * -1)
DolphinDB:
  def gtjaAlpha148(open, vol){
      return (rowRank(mcorr(open, msum(mavg(vol, 60), 9), 6), percent=true)
              < rowRank(open - mmin(open, 14), percent=true)) * (-1)
  }

翻译要点:
- 左侧 = RANK(CORR(OPEN, SUM(MEAN(VOL,60),9), 6))
  = 过去6日 (开盘 vs 9日(60日量均值)求和) 的时序相关，横截面排名。
- 右侧 = RANK(OPEN - TSMIN(OPEN,14)) = 开盘相对14日开盘最低的溢价，横截面排名。
- (left < right) 布尔 * -1 → true=-1, false=0。
- rowRank 横截面 → rolling 时序 pct rank 近似（有损），含前导NaN用 min_periods=1。
- 最长链：mavg(60)+msum(9)+mcorr(6) = 75；右侧 mmin(14)。

语义: 布尔因子(-1/0)。当"开盘与中长期量和的相关排名" < "开盘相对14日低点溢价排名"时为 -1。
      含多层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_corr, ts_min, ts_sum


class Alpha148Factor(FactorBase):
    name = "gtja_alpha148"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 75:  # mavg(60)+msum(9)+mcorr(6) = 75
            return None
        op, vol = df["open"], df["volume"]
        mv60 = vol.rolling(60).mean()              # MEAN(VOL,60)
        s_v = ts_sum(mv60, 9)                      # SUM(MEAN(VOL,60),9)
        corr_left = ts_corr(op, s_v, 6)            # CORR(OPEN, ..., 6)
        left = corr_left.rolling(10, min_periods=1).rank(pct=True)
        tsmin14 = ts_min(op, 14)                   # TSMIN(OPEN,14)
        right = (op - tsmin14).rolling(10, min_periods=1).rank(pct=True)
        cmp = (left < right).astype(float) * (-1.0)
        val = cmp.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
