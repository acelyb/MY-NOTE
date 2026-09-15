"""
GTJA191 Alpha123 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (RANK(CORR(SUM(((HIGH+LOW)/2),20), SUM(MEAN(VOLUME,60),20), 9))
    < RANK(CORR(LOW, VOLUME, 6))) * -1
DolphinDB:
  def gtjaAlpha123(high, low, vol){
      return (rowRank(mcorr(msum((high + low) \ 2, 20), msum(mavg(vol, 60), 20), 9), percent=true)
              < rowRank(mcorr(low, vol, 6), percent=true)) * (-1)
  }

翻译要点:
- 左侧 = RANK(CORR(SUM((H+L)/2,20), SUM(MEAN(VOL,60),20), 9))
  = 过去9日 [20日(H+L)/2求和 vs 20日(60日量均值)求和] 的时序相关，横截面排名。
- 右侧 = RANK(CORR(LOW, VOLUME, 6)) = 过去6日(低价,量)时序相关，横截面排名。
- (left < right) 布尔比较 * -1 → true=-1, false=0。
- rowRank 横截面 → rolling 时序 pct rank 近似（有损）。
- ⚠️ 含多层前导 NaN：mavg(60)+msum(20)+mcorr(9)；rowRank 用 min_periods=1。

语义: 布尔因子(-1/0)。当"中长期量价相关排名" < "短期低价量相关排名"时为 -1。
  含多层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_corr, ts_sum


class Alpha123Factor(FactorBase):
    name = "gtja_alpha123"

    def calc(self, df: pd.DataFrame) -> float | None:
        # 最长链: mavg(60)+msum(20)+mcorr(9) → 89；右侧 mcorr(6)
        if len(df) < 89:
            return None
        high, low, vol = df["high"], df["low"], df["volume"]
        hl2 = (high + low) / 2
        s_hl = ts_sum(hl2, 20)                     # SUM((H+L)/2,20)
        mv60 = vol.rolling(60).mean()              # MEAN(VOL,60)
        s_v = ts_sum(mv60, 20)                     # SUM(MEAN(VOL,60),20)
        corr_left = ts_corr(s_hl, s_v, 9)          # CORR(...,9)
        left = corr_left.rolling(10, min_periods=1).rank(pct=True)
        corr_right = ts_corr(low, vol, 6)          # CORR(LOW,VOL,6)
        right = corr_right.rolling(10, min_periods=1).rank(pct=True)
        cmp = (left < right).astype(float) * (-1.0)
        val = cmp.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
