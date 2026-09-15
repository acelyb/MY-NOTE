"""
GTJA191 Alpha1 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  -1 * CORR(RANK(DELTA(LOG(VOLUME),1)), RANK((CLOSE-OPEN)/OPEN), 6)
DolphinDB:
  def gtjaAlpha1(open, close, vol){
      delta = log(vol) - mfirst(log(vol), 2)
      return -1 * (mcorr(rowRank(delta, percent=true), rowRank((close - open) \ open, percent=true), 6))
  }

翻译要点:
- delta = LOG(VOL) - LOG(VOL_{t-1}) = 量的对数日变化(≈量变化率)。
- (CLOSE-OPEN)/OPEN = 日内收益率(开收比)。
- 两个 rowRank 横截面排名；mcorr(量变化排名, 日内收益排名, 6)=过去6日两者的时序相关。
- 整体取负。
- 单标的口径：rowRank 横截面 → 用 rolling(6) 时序 pct rank 近似（与 alpha5/alpha99 同思路，有损）。
- log(vol) 中 vol<=0 时为 nan（停牌/零量），自然剔除。

语义: 量变化与日内收益的6日时序相关，取负。
  与 alpha5(量-高价排名相关)、alpha99(量价协方差) 同属"量价相关"维度，但口径不同：
  alpha1 用"量的对数变化"×"日内开收收益"，强调量变与日内涨跌的同步性。
  量价同向(放量涨)→相关高→取负后小→预期未来收益低(量价背离反转)。
  含横截面 rowRank 近似（双重有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha1Factor(FactorBase):
    name = "gtja_alpha1"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 12:  # rank(6) + corr(6)
            return None
        op, close, vol = df["open"], df["close"], df["volume"]
        lnvol = np.log(vol.replace(0, np.nan))
        delta = lnvol - lnvol.shift(1)
        intraret = (close - op) / op
        r1 = delta.rolling(6).rank(pct=True)
        r2 = intraret.rolling(6).rank(pct=True)
        corr6 = r1.rolling(6).corr(r2)
        val = (-corr6).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
